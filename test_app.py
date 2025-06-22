#!/usr/bin/env python3
"""
Test script for LegisWatch application
Run this to verify the application is working correctly
"""

import sys
import os
import requests
import subprocess
import time
import threading
from werkzeug.serving import make_server

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        import requests
        from app import app, BillTracker
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_bill_tracker():
    """Test the BillTracker class functionality"""
    print("Testing BillTracker...")
    try:
        from app import BillTracker
        tracker = BillTracker()
        
        # Test keyword search
        bills = tracker.search_bills_by_keyword("healthcare", limit=5)
        assert isinstance(bills, list), "search_bills_by_keyword should return a list"
        print(f"✓ Keyword search returned {len(bills)} bills")
        
        # Test state search
        bills = tracker.search_bills_by_state("CA", limit=5)
        assert isinstance(bills, list), "search_bills_by_state should return a list"
        print(f"✓ State search returned {len(bills)} bills")

        # Test state normalization
        state_abbr = tracker._normalize_state("California")
        assert state_abbr == "CA", "_normalize_state should return state abbreviation"
        print("✓ State normalization working")

        return True
    except Exception as e:
        print(f"✗ BillTracker test failed: {e}")
        return False

def test_flask_app():
    """Test Flask application routes"""
    print("Testing Flask app...")
    try:
        from app import app
        
        with app.test_client() as client:
            # Test main page
            response = client.get('/')
            assert response.status_code == 200, f"Main page returned {response.status_code}"
            print("✓ Main page loads successfully")
            
            # Test health endpoint
            response = client.get('/health')
            assert response.status_code == 200, f"Health endpoint returned {response.status_code}"
            print("✓ Health endpoint working")
            
            # Test search API
            response = client.post('/api/search', 
                                 json={'query': 'test', 'type': 'keyword', 'include_ai': False})
            assert response.status_code == 200, f"Search API returned {response.status_code}"
            print("✓ Search API working")
            
        return True
    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        return False

def test_server_startup():
    """Test that the server can start successfully"""
    print("Testing server startup...")
    try:
        from app import app
        
        # Start server in a separate thread
        server = make_server('127.0.0.1', 5001, app, threaded=True)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Test if server responds
        response = requests.get('http://127.0.0.1:5001/health', timeout=5)
        assert response.status_code == 200, f"Server health check failed: {response.status_code}"
        
        # Shutdown server
        server.shutdown()
        
        print("✓ Server startup and health check successful")
        return True
    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("=" * 50)
    print("LegisWatch Application Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("BillTracker Tests", test_bill_tracker),
        ("Flask App Tests", test_flask_app),
        ("Server Startup Tests", test_server_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        if test_func():
            passed += 1
        else:
            print("Test failed!")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LegisWatch is ready to run.")
        print("\nTo start the application, run:")
        print("python app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Missing dependencies (run: pip install -r requirements.txt)")
        print("- Python version compatibility (requires Python 3.8+)")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
