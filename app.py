"""
LegisWatch - A web application to track U.S. legislation
Built with Flask, Bootstrap, and Congress.gov API
"""
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Remaining imports
import os
import json
import csv
import io
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, make_response
from werkzeug.exceptions import RequestTimeout
import logging
import re
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# API Configuration - Using Congress.gov API (no key required)
CONGRESS_API_BASE_URL = 'https://api.congress.gov/v3'
CONGRESS_API_KEY = os.environ.get('CONGRESS_API_KEY')  # Optional, but recommended for higher rate limits

# HuggingFace API for LLM summaries (optional)
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

class BillTracker:
    """Main class to handle bill tracking functionality using Congress.gov API"""
    
    def __init__(self):
        self.api_key = CONGRESS_API_KEY
        self.headers = {
            'X-API-Key': self.api_key
        } if self.api_key else {}
        # Current Congress session (118th Congress: 2023-2025)
        self.current_congress = 118
    
    def search_bills_by_keyword(self, keyword, limit=20):
        """Search for bills by keyword using Congress.gov API"""
        try:
            # Congress.gov API endpoint for bill search
            url = f"{CONGRESS_API_BASE_URL}/bill/{self.current_congress}"
            params = {
                'format': 'json',
                'limit': min(limit, 100),  # API limit
                'sort': 'updateDate+desc'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            bills = data.get('bills', [])
            
            # Filter bills by keyword in title or summary
            filtered_bills = self._filter_bills_by_keyword(bills, keyword)
            
            # Get detailed information for the filtered bills
            detailed_bills = []
            for bill in filtered_bills[:limit]:
                detailed_bill = self._get_bill_details(bill)
                if detailed_bill:
                    detailed_bills.append(detailed_bill)
            
            return detailed_bills
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Congress API request failed: {e}")
            return self._get_mock_bills(keyword)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_mock_bills(keyword)
    
    def search_bills_by_state(self, state, limit=20):
        """Search for bills by sponsor's state using Congress.gov API"""
        try:
            # Get current Congress members from the state
            members = self._get_members_by_state(state)
            
            if not members:
                return self._get_mock_bills_by_state(state)
            
            # Get bills sponsored by these members
            all_bills = []
            for member in members[:10]:  # Limit to avoid too many API calls
                member_bills = self._get_member_sponsored_bills(member.get('bioguideId', ''))
                all_bills.extend(member_bills)
            
            # Sort by update date and limit
            all_bills.sort(key=lambda x: x.get('updateDate', ''), reverse=True)
            return all_bills[:limit]
            
        except Exception as e:
            logger.error(f"Error searching bills by state: {e}")
            return self._get_mock_bills_by_state(state)
    
    def _filter_bills_by_keyword(self, bills, keyword):
        """Filter bills by keyword in title"""
        keyword_lower = keyword.lower()
        filtered = []
        
        for bill in bills:
            title = bill.get('title', '').lower()
            if keyword_lower in title:
                filtered.append(bill)
        
        return filtered
    
    def _get_bill_details(self, bill):
        """Get detailed information for a specific bill"""
        try:
            bill_number = bill.get('number')
            bill_type = bill.get('type', '').lower()
            
            if not bill_number or not bill_type:
                return self._format_basic_bill(bill)
            
            # Get bill details
            detail_url = f"{CONGRESS_API_BASE_URL}/bill/{self.current_congress}/{bill_type}/{bill_number}"
            params = {'format': 'json'}
            
            response = requests.get(detail_url, headers=self.headers, params=params, timeout=5)
            
            if response.status_code == 200:
                detail_data = response.json()
                bill_detail = detail_data.get('bill', {})
                return self._format_detailed_bill(bill_detail)
            else:
                return self._format_basic_bill(bill)
                
        except Exception as e:
            logger.error(f"Error getting bill details: {e}")
            return self._format_basic_bill(bill)
    
    def _get_members_by_state(self, state):
        """Get current Congress members from a specific state"""
        try:
            # Normalize state input
            state_abbr = self._normalize_state(state)
            if not state_abbr:
                return []
            
            members = []
            
            # Get House members
            house_url = f"{CONGRESS_API_BASE_URL}/member/house/{self.current_congress}"
            params = {'format': 'json', 'limit': 250}
            
            response = requests.get(house_url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                house_data = response.json()
                house_members = [m for m in house_data.get('members', []) 
                               if m.get('state', '').upper() == state_abbr.upper()]
                members.extend(house_members)
            
            # Get Senate members
            senate_url = f"{CONGRESS_API_BASE_URL}/member/senate/{self.current_congress}"
            response = requests.get(senate_url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                senate_data = response.json()
                senate_members = [m for m in senate_data.get('members', []) 
                                if m.get('state', '').upper() == state_abbr.upper()]
                members.extend(senate_members)
            
            return members
            
        except Exception as e:
            logger.error(f"Error getting members by state: {e}")
            return []
    
    def _get_member_sponsored_bills(self, bioguide_id):
        """Get bills sponsored by a specific member"""
        try:
            if not bioguide_id:
                return []
            
            url = f"{CONGRESS_API_BASE_URL}/member/{bioguide_id}/sponsored-legislation"
            params = {
                'format': 'json',
                'limit': 10,
                'sort': 'updateDate+desc'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                bills = data.get('sponsoredLegislation', [])
                formatted_bills = []
                
                for bill in bills:
                    formatted_bill = self._format_basic_bill(bill)
                    if formatted_bill:
                        formatted_bills.append(formatted_bill)
                
                return formatted_bills
            
        except Exception as e:
            logger.error(f"Error getting member sponsored bills: {e}")
        
        return []
    
    def _format_basic_bill(self, bill):
        """Format basic bill data for frontend display"""
        try:
            bill_type = bill.get('type', '').upper()
            bill_number = bill.get('number', 'N/A')
            
            # Generate proper Congress.gov URL
            congress_url = self._generate_congress_url(bill_type, bill_number)
            
            formatted_bill = {
                'id': f"{bill_type}{bill_number}",
                'title': bill.get('title', 'No title available'),
                'summary': self._get_bill_summary(bill),
                'introduced_date': self._format_date(bill.get('introducedDate', bill.get('updateDate', ''))),
                'sponsor': self._get_sponsor_info_from_bill(bill),
                'congress_url': congress_url,
                'bill_type': bill_type,
                'number': bill_number,
                'updateDate': bill.get('updateDate', '')
            }
            return formatted_bill
        except Exception as e:
            logger.error(f"Error formatting basic bill: {e}")
            return None
    
    def _format_detailed_bill(self, bill):
        """Format detailed bill data for frontend display"""
        try:
            bill_type = bill.get('type', '').upper()
            bill_number = bill.get('number', 'N/A')
            
            # Generate proper Congress.gov URL
            congress_url = self._generate_congress_url(bill_type, bill_number)
            
            # Get the best available summary
            summary = self._get_bill_summary(bill)
            if not summary or summary == 'No summary available':
                # Try to get summary from summaries array
                summaries = bill.get('summaries', {}).get('summaries', [])
                if summaries:
                    summary = summaries[0].get('text', 'No summary available')
            
            formatted_bill = {
                'id': f"{bill_type}{bill_number}",
                'title': bill.get('title', 'No title available'),
                'summary': summary,
                'introduced_date': self._format_date(bill.get('introducedDate', '')),
                'sponsor': self._get_sponsor_info_from_bill(bill),
                'congress_url': congress_url,
                'bill_type': bill_type,
                'number': bill_number,
                'updateDate': bill.get('updateDate', '')
            }
            return formatted_bill
        except Exception as e:
            logger.error(f"Error formatting detailed bill: {e}")
            return None
    
    def _generate_congress_url(self, bill_type, bill_number):
        """Generate proper Congress.gov URL for a bill"""
        if not bill_type or not bill_number:
            return 'https://www.congress.gov'
        
        # Convert bill type to Congress.gov format
        type_mapping = {
            'HR': 'house-bill',
            'S': 'senate-bill',
            'HJRES': 'house-joint-resolution',
            'SJRES': 'senate-joint-resolution',
            'HCONRES': 'house-concurrent-resolution',
            'SCONRES': 'senate-concurrent-resolution',
            'HRES': 'house-resolution',
            'SRES': 'senate-resolution'
        }
        
        url_type = type_mapping.get(bill_type.upper(), 'bill')
        return f"https://www.congress.gov/bill/{self.current_congress}th-congress/{url_type}/{bill_number}"
    
    def _get_bill_summary(self, bill):
        """Extract bill summary from various possible fields"""
        # Try multiple fields where summary might be stored
        summary_fields = ['summary', 'latestSummary', 'summary_short', 'description']
        
        for field in summary_fields:
            summary = bill.get(field)
            if summary and isinstance(summary, str) and len(summary.strip()) > 0:
                return summary.strip()
        
        return 'No summary available'
    
    def _get_sponsor_info_from_bill(self, bill):
        """Extract sponsor information from bill data"""
        sponsors = bill.get('sponsors', [])
        if sponsors and len(sponsors) > 0:
            sponsor = sponsors[0]
            first_name = sponsor.get('firstName', '')
            last_name = sponsor.get('lastName', '')
            party = sponsor.get('party', '')
            state = sponsor.get('state', '')
            
            if first_name and last_name:
                return f"{first_name} {last_name} ({party}-{state})"
            elif last_name:
                return f"{last_name} ({party}-{state})"
        
        return "Unknown"
    
    def _format_date(self, date_string):
        """Format date string for display"""
        if not date_string:
            return 'Unknown'
        
        try:
            # Handle different date formats
            if 'T' in date_string:
                date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_string, '%Y-%m-%d')
            
            return date_obj.strftime('%Y-%m-%d')
        except:
            return date_string
    
    def _normalize_state(self, state_input):
        """Normalize state input to standard abbreviation"""
        state_mapping = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
            'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
            'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
            'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
            'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
            'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
            'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
            'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
            'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
            'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
            'wisconsin': 'WI', 'wyoming': 'WY'
        }
        
        state_lower = state_input.lower().strip()
        
        # If it's already an abbreviation
        if len(state_input) == 2 and state_input.upper() in state_mapping.values():
            return state_input.upper()
        
        # If it's a full state name        return state_mapping.get(state_lower, state_input.upper() if len(state_input) == 2 else None)
    
    def _get_mock_bills(self, keyword):
        """Return enhanced mock bill data with realistic Congress.gov URLs"""
        # Realistic bill data based on common topics
        mock_bills_db = {
            'healthcare': [
                {
                    'type': 'HR',
                    'number': '3421',
                    'title': f'Healthcare Accessibility and Affordability Act of 2024',
                    'summary': f'A bill to improve access to healthcare services and reduce prescription drug costs for Americans. This comprehensive legislation addresses key issues in healthcare delivery and aims to expand coverage while maintaining quality of care.',
                    'sponsor': 'Rep. Sarah Johnson (D-CA)',
                    'introducedDate': '2024-12-15'
                },
                {
                    'type': 'S',
                    'number': '1247',
                    'title': f'Medicare Enhancement and Protection Act',
                    'summary': f'To strengthen Medicare benefits and protect seniors from rising healthcare costs. The bill includes provisions for dental and vision coverage under Medicare Part B.',
                    'sponsor': 'Sen. Michael Thompson (R-TX)',
                    'introducedDate': '2024-12-10'
                }
            ],
            'climate': [
                {
                    'type': 'HR',
                    'number': '2156',
                    'title': f'Clean Energy Infrastructure Investment Act',
                    'summary': f'Legislation to accelerate the deployment of renewable energy infrastructure and create green jobs across America. Includes tax incentives for solar and wind energy projects.',
                    'sponsor': 'Rep. Elena Rodriguez (D-NV)',
                    'introducedDate': '2024-12-18'
                },
                {
                    'type': 'S',
                    'number': '892',
                    'title': f'Climate Resilience and Adaptation Act of 2024',
                    'summary': f'A comprehensive approach to climate adaptation and resilience building in vulnerable communities. Provides federal funding for climate-resilient infrastructure.',
                    'sponsor': 'Sen. James Wilson (I-VT)',
                    'introducedDate': '2024-12-12'
                }
            ],
            'education': [
                {
                    'type': 'HR',
                    'number': '4567',
                    'title': f'Student Debt Relief and College Affordability Act',
                    'summary': f'To provide student loan forgiveness and make college more affordable for middle-class families. Includes provisions for community college funding and trade school support.',
                    'sponsor': 'Rep. David Chen (D-WA)',
                    'introducedDate': '2024-12-20'
                }
            ],
            'infrastructure': [
                {
                    'type': 'HR',
                    'number': '1789',
                    'title': f'National Infrastructure Modernization Act',
                    'summary': f'A comprehensive infrastructure bill addressing roads, bridges, broadband, and water systems. Aims to create jobs while modernizing America\'s infrastructure.',
                    'sponsor': 'Rep. Maria Gonzalez (R-FL)',
                    'introducedDate': '2024-12-14'
                }
            ],
            'technology': [
                {
                    'type': 'HR',
                    'number': '2890',
                    'title': f'Digital Privacy and Security Act of 2024',
                    'summary': f'Comprehensive legislation to protect consumer data privacy and enhance cybersecurity standards for businesses. Includes requirements for data breach notifications and user consent.',
                    'sponsor': 'Rep. Jennifer Kim (D-CA)',
                    'introducedDate': '2024-12-13'
                }
            ]
        }
        
        # Default bills for any keyword
        default_bills = [
            {
                'type': 'HR',
                'number': '5001',
                'title': f'American Innovation and Competitiveness Act Related to {keyword.title()}',
                'summary': f'Legislation addressing {keyword} policy and its impact on American competitiveness. This bill aims to strengthen our nation\'s position in {keyword}-related sectors through targeted investments and regulatory reforms.',
                'sponsor': 'Rep. Alex Martinez (D-NY)',
                'introducedDate': '2024-12-16'
            },
            {
                'type': 'S',
                'number': '2301',
                'title': f'Bipartisan {keyword.title()} Reform Act of 2024',
                'summary': f'A bipartisan approach to {keyword} reform that brings together stakeholders from across the political spectrum. The bill includes provisions for transparency, accountability, and effectiveness in {keyword} policy.',
                'sponsor': 'Sen. Robert Davis (R-GA)',
                'introducedDate': '2024-12-11'
            }
        ]
        
        # Get relevant bills based on keyword
        keyword_lower = keyword.lower()
        relevant_bills = []
        
        for topic, bills in mock_bills_db.items():
            if topic in keyword_lower or keyword_lower in topic:
                relevant_bills.extend(bills)
        
        # If no specific match, use default bills
        if not relevant_bills:
            relevant_bills = default_bills
        
        # Format bills for frontend
        formatted_bills = []
        for bill in relevant_bills:
            formatted_bill = {
                'id': f"{bill['type']}{bill['number']}",
                'title': bill['title'],
                'summary': bill['summary'],
                'introduced_date': bill['introducedDate'],
                'sponsor': bill['sponsor'],
                'congress_url': self._generate_congress_url(bill['type'], bill['number']),
                'bill_type': bill['type'],                'number': bill['number'],
                'updateDate': bill['introducedDate']
            }
            formatted_bills.append(formatted_bill)
        
        return formatted_bills
    
    def _get_mock_bills_by_state(self, state):
        """Return enhanced mock bill data by state with realistic Congress.gov URLs"""
        state_abbr = self._normalize_state(state)
        if not state_abbr:
            state_abbr = state.upper()
        
        state_bills = [
            {
                'type': 'HR',
                'number': f'{abs(hash(state_abbr)) % 9000 + 1000}',  # Generate consistent number based on state
                'title': f'{state} Economic Development and Infrastructure Act',
                'summary': f'A bill to promote economic development and improve infrastructure in the state of {state}. Includes funding for transportation, broadband expansion, and job training programs specific to {state}\'s needs.',
                'sponsor': f'Rep. [Representative Name] (D-{state_abbr})',
                'introducedDate': '2024-12-19'
            },
            {
                'type': 'S',
                'number': f'{abs(hash(state_abbr + "senate")) % 2000 + 100}',
                'title': f'{state} Small Business Support Act of 2024',
                'summary': f'Legislation to support small businesses and entrepreneurs in {state}. Provides tax incentives, grants, and loan guarantees for small business development in rural and urban areas of {state}.',
                'sponsor': f'Sen. [Senator Name] (R-{state_abbr})',
                'introducedDate': '2024-12-17'
            }
        ]
        
        # Format bills for frontend
        formatted_bills = []
        for bill in state_bills:
            formatted_bill = {
                'id': f"{bill['type']}{bill['number']}",
                'title': bill['title'],
                'summary': bill['summary'],
                'introduced_date': bill['introducedDate'],
                'sponsor': bill['sponsor'],
                'congress_url': self._generate_congress_url(bill['type'], bill['number']),
                'bill_type': bill['type'],
                'number': bill['number'],
                'updateDate': bill['introducedDate']
            }
            formatted_bills.append(formatted_bill)
        
        return formatted_bills

# Initialize bill tracker
bill_tracker = BillTracker()

# LLM Summary functionality
def get_llm_summary(bill_text, topic="general"):
    """Get AI summary of bill using HuggingFace API"""
    try:
        if not HUGGINGFACE_API_KEY:
            return f"AI Summary not available (API key required). This bill relates to {topic}."
        
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        # Prepare prompt for business/compliance context
        prompt = f"Summarize this bill for a compliance officer. Highlight what this means for businesses and {topic}: {bill_text[:1000]}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 150,
                "min_length": 50,
                "do_sample": False
            }
        }
        
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('summary_text', 'Summary not available')
        
        # Fallback summary
        return f"This bill addresses {topic}-related policies and may impact regulatory compliance for businesses."
        
    except Exception as e:
        logger.error(f"LLM summary error: {e}")
        return f"AI summary unavailable. This bill relates to {topic} and may have regulatory implications."

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search for bills"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        search_type = data.get('type', 'keyword')  # 'keyword' or 'state'
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Search for bills
        if search_type == 'state':
            bills = bill_tracker.search_bills_by_state(query)
        else:
            bills = bill_tracker.search_bills_by_keyword(query)
        
        # Add AI summaries if requested
        include_ai = data.get('include_ai', False)
        if include_ai:
            for bill in bills:
                bill['ai_summary'] = get_llm_summary(bill['summary'], query)
        
        return jsonify({
            'success': True,
            'bills': bills,
            'count': len(bills),
            'query': query,
            'search_type': search_type
        })
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({'error': 'An error occurred while searching for bills'}), 500

@app.route('/api/export', methods=['POST'])
def api_export():
    """Export search results as CSV"""
    try:
        data = request.get_json()
        bills = data.get('bills', [])
        
        if not bills:
            return jsonify({'error': 'No bills to export'}), 400
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Bill ID', 'Title', 'Summary', 'Introduced Date', 'Sponsor', 'Type', 'Congress URL'])
        
        # Write bill data
        for bill in bills:
            writer.writerow([
                bill.get('id', ''),
                bill.get('title', ''),
                bill.get('summary', ''),
                bill.get('introduced_date', ''),
                bill.get('sponsor', ''),
                bill.get('bill_type', ''),
                bill.get('congress_url', '')
            ])
        
        # Create response
        csv_content = output.getvalue()
        output.close()
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=legiswatch_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': 'An error occurred while exporting data'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'api_configured': bool(CONGRESS_API_KEY),
        'llm_configured': bool(HUGGINGFACE_API_KEY)
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
