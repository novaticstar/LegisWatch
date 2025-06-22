# LegisWatch Deployment Guide

This guide covers deploying LegisWatch to various cloud platforms.

## 🌐 Quick Deploy Options

### Option 1: Render (Recommended - Free Tier Available)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. **Fork this repository** to your GitHub account
2. **Sign up for Render** at [render.com](https://render.com)
3. **Create a new Web Service**:
   - Connect your GitHub repository
   - Choose the branch (usually `main`)
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. **Set Environment Variables**:
   - `CONGRESS_API_KEY`: Your Congress.gov API key
   - `HUGGINGFACE_API_KEY`: Your HuggingFace API token
   - `SECRET_KEY`: A secure random string
5. **Deploy**: Render will automatically build and deploy your app

### Option 2: Heroku

1. **Install Heroku CLI** from [devcenter.heroku.com](https://devcenter.heroku.com/articles/heroku-cli)
2. **Login and create app**:
```bash
heroku login
heroku create your-legiswatch-app
```
3. **Set environment variables**:
```bash
heroku config:set CONGRESS_API_KEY=your_api_key
heroku config:set HUGGINGFACE_API_KEY=your_hf_token
heroku config:set SECRET_KEY=your_secret_key
```
4. **Deploy**:
```bash
git push heroku main
```

### Option 3: Railway

1. **Sign up** at [railway.app](https://railway.app)
2. **Connect GitHub repository**
3. **Set environment variables** in Railway dashboard
4. **Deploy**: Railway will auto-deploy from your repository

### Option 4: PythonAnywhere

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)
2. **Upload your code** via Git or file upload
3. **Create a web app** with manual configuration
4. **Configure WSGI file**:
```python
import sys
import os

# Add your project directory to the Python path
sys.path.append('/home/yourusername/LegisWatch')

# Set environment variables
os.environ['PROPUBLICA_API_KEY'] = 'your_api_key'
os.environ['HUGGINGFACE_API_KEY'] = 'your_hf_token'
os.environ['SECRET_KEY'] = 'your_secret_key'

from app import app as application
```

## 🔧 Local Development

### Using Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  legiswatch:
    build: .
    ports:
      - "5000:5000"
    environment:
      - PROPUBLICA_API_KEY=${PROPUBLICA_API_KEY}
      - HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env
```

Build and run:
```bash
docker-compose up --build
```

### Using Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key for sessions |
| `CONGRESS_API_KEY` | Optional | Congress.gov API key |
| `HUGGINGFACE_API_KEY` | Optional | HuggingFace API token for AI summaries |
| `DEBUG` | No | Set to `True` for development |
| `PORT` | No | Port to run the app (default: 5000) |

## 🚀 Production Considerations

### Security
- Use a strong `SECRET_KEY`
- Enable HTTPS in production
- Consider rate limiting for API endpoints
- Validate all user inputs

### Performance
- Use a production WSGI server (Gunicorn included)
- Consider caching frequently accessed data
- Implement API response caching
- Use a CDN for static assets

### Monitoring
- Set up error tracking (e.g., Sentry)
- Monitor API usage and limits
- Track application performance
- Set up health check monitoring

### Scaling
- Use environment variables for configuration
- Consider using Redis for session storage
- Implement database for user data if needed
- Use load balancers for high traffic

## 🛠️ Troubleshooting

### Common Issues

**App won't start:**
- Check all environment variables are set
- Verify Python version (3.8+ required)
- Check requirements.txt dependencies

**API errors:**
- Verify API keys are correct
- Check API rate limits
- Ensure network connectivity

**Styling issues:**
- Verify Bootstrap CDN is accessible
- Check for JavaScript console errors
- Ensure templates directory exists

### Debug Mode

To enable debug mode locally:
```bash
export DEBUG=True  # Linux/macOS
set DEBUG=True     # Windows
python app.py
```

### Logs

Check application logs:
```bash
# Heroku
heroku logs --tail

# Render
# Check logs in Render dashboard

# Local
# Logs appear in terminal where app is running
```

## 📊 Performance Monitoring

Add basic performance monitoring:

```python
import time
from functools import wraps

def monitor_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        print(f"{f.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return decorated_function
```

## 🔄 CI/CD Pipeline

Example GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python test_app.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Render
      # Add deployment steps here
      run: echo "Deploy to your platform"
```

## 📈 Scaling Considerations

### Database Integration
If you need to store user data or search history:

```python
# Example with SQLite
import sqlite3

def init_db():
    conn = sqlite3.connect('legiswatch.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY,
            query TEXT,
            search_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()
```

### Caching
Implement caching for API responses:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_api_call(query, search_type):
    # Your API call here
    pass
```

### Background Jobs
For periodic bill updates:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=update_bills,
    trigger="interval",
    hours=6
)
scheduler.start()
```

---

**Need help with deployment?** Open an issue on GitHub or check the documentation for your chosen platform.
