# LegisWatch 🏛️

**Real-Time U.S. Bill Tracker with AI-Powered Insights**

LegisWatch is a modern, full-stack web application that allows users to search and track newly proposed U.S. bills by state or policy topic. Built with Python Flask and Bootstrap, it features an intuitive interface and optional AI-powered summaries to help users understand complex legislation.

![LegisWatch Preview](https://via.placeholder.com/800x400/667eea/white?text=LegisWatch+Screenshot+Here)

## ✨ Features

- 🔍 **Smart Search**: Search bills by topic keywords or U.S. state
- 🤖 **AI Summaries**: Get business/compliance-focused bill summaries using HuggingFace models
- 📊 **Responsive Design**: Modern, mobile-friendly interface built with Bootstrap 5
- 📁 **Export Functionality**: Download search results as CSV files
- ⚡ **Real-time Updates**: Asynchronous search with live results
- 🛡️ **Error Handling**: Graceful fallbacks and user-friendly error messages
- 📱 **Mobile Optimized**: Works seamlessly on all devices

## 🚀 Tech Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **APIs**: Congress.gov API, HuggingFace Inference API
- **Deployment**: Gunicorn, supports Heroku/Render deployment

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/LegisWatch.git
cd LegisWatch
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
```

### 5. Get API Keys (Optional but Recommended)

#### Congress.gov API (Free)
1. Visit [Congress.gov API](https://api.congress.gov/sign-up/)
2. Sign up for a free API key
3. Add your key to `.env`: `CONGRESS_API_KEY=your_key_here`

#### HuggingFace API (Free - for AI summaries)
1. Visit [HuggingFace](https://huggingface.co/settings/tokens)
2. Create a free account and generate an API token
3. Add your token to `.env`: `HUGGINGFACE_API_KEY=your_token_here`

> **Note**: The app works without API keys using mock data for demonstration purposes.

### 6. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` in your browser to start using LegisWatch!

## 🎯 Usage

### Basic Search
1. Enter a topic (e.g., "healthcare", "climate change") or state name/abbreviation
2. Select search type: "By Topic/Keyword" or "By State"
3. Optionally enable AI summaries for business context
4. Click "Search Bills" to see results

### Advanced Features
- **Export Results**: Click "Export CSV" to download your search results
- **Copy Bill Info**: Use the copy button on any bill card to copy details to clipboard
- **Keyboard Shortcuts**: 
  - `Ctrl/Cmd + /`: Focus search input
  - `Ctrl/Cmd + Enter`: Trigger search from anywhere

### Example Searches
- **Topics**: healthcare reform, climate change, infrastructure, education funding
- **States**: California, CA, Texas, TX, New York, NY

## 🌐 API Endpoints

### `POST /api/search`
Search for bills by keyword or state.

**Request Body:**
```json
{
  "query": "healthcare",
  "type": "keyword",
  "include_ai": true
}
```

**Response:**
```json
{
  "success": true,
  "bills": [...],
  "count": 10,
  "query": "healthcare",
  "search_type": "keyword"
}
```

### `POST /api/export`
Export search results as CSV.

### `GET /health`
Health check endpoint for monitoring.

## 📁 Project Structure

```
LegisWatch/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Frontend HTML template
├── requirements.txt      # Python dependencies
├── Procfile             # Deployment configuration
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## 🧪 Testing

The application includes comprehensive error handling and fallback mechanisms:

- **API Failures**: Graceful fallback to mock data
- **Network Issues**: User-friendly error messages
- **Invalid Inputs**: Input validation and helpful prompts
- **No Results**: Clear messaging with search suggestions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Congress.gov API](https://api.congress.gov/) for official U.S. legislative data
- [HuggingFace](https://huggingface.co/) for AI model hosting
- [Bootstrap](https://getbootstrap.com/) for responsive UI components
- [Font Awesome](https://fontawesome.com/) for icons

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/novaticstar/LegisWatch/issues) page
2. Create a new issue with detailed information
3. For urgent matters, contact [mattmwork2022@gmail.com]

## 🔮 Planned Future Enhancements

- 📧 Email notifications for new bills
- 💾 User accounts and saved searches
- 📈 Bill tracking analytics
- 🗄️ Database integration for search history
- 📅 Scheduled bill monitoring
- 🔍 Advanced filtering options

---

**Built with ❤️ for transparency and civic engagement**
