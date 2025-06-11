# 🤖 Enhanced FAQ Chatbot

A robust, production-ready FAQ chatbot powered by OpenAI's function-calling capabilities and built with FastAPI. The chatbot intelligently routes questions to appropriate FAQ categories (Sales, Labs, Reports) and provides accurate, context-aware responses.

## 🌟 Features

- **Intelligent Question Classification**: Automatically routes questions to appropriate knowledge sources
- **Multi-Language Support**: Supports Traditional Chinese, Simplified Chinese, and English
- **FAQ Integration**: Access to comprehensive business FAQ database
- **Database Querying**: Real-time pathogen database statistics and organism information
- **Modern Web Interface**: Clean, responsive UI with typing indicators
- **Conversation Memory**: Maintains context across multiple questions
- **Error Handling**: Comprehensive error handling with helpful feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key

### Installation

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd FAQbot
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **Run the application:**
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

5. **Open your browser:**
```
http://localhost:8000
```

## 📁 Project Structure

```
FAQbot/
├── app/                    # Main application package
│   ├── models/            # Pydantic data models
│   ├── services/          # Business logic services
│   ├── api/              # API routes and endpoints
│   ├── utils/            # Utilities (logging, exceptions)
│   ├── config.py         # Configuration management
│   └── main.py           # FastAPI application
├── faqs/                 # FAQ content files
│   ├── sales.txt
│   ├── labs.txt
│   └── reports.txt
├── frontend/             # Web interface
│   ├── templates/        # Jinja2 templates
│   └── static/          # CSS and JavaScript
├── tests/               # Test suite
└── requirements.txt     # Python dependencies
```

## 🛠️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (with defaults)
OPENAI_MODEL=gpt-4-1106-preview
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.1

APP_NAME=FAQ Chatbot
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

HOST=0.0.0.0
PORT=8000
RELOAD=False

CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:8000"]
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

## 📚 API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /` - Web chat interface
- `POST /api/chat` - Send a question and get an AI response
- `GET /api/health` - Health check endpoint

### Example API Usage

```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are your pricing plans?"}'
```

Response:
```json
{
  "answer": "We offer three pricing tiers: Starter ($29/month), Professional ($79/month), and Enterprise ($199/month). Each plan includes different features and usage limits.",
  "category": "sales",
  "conversation_id": "uuid-string",
  "processing_time": 1.234
}
```

## 📝 Managing FAQ Content

FAQ files are stored in the `faqs/` directory as plain text files:

### Format
```
CATEGORY FAQ

Q: Question 1?
A: Answer to question 1.

Q: Question 2?
A: Answer to question 2.
```

### Adding New Categories

1. Create a new `.txt` file in `faqs/` directory
2. Add the category to `FAQCategory` enum in `app/models/schemas.py`
3. Restart the application

## 🧪 Testing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py
```

## 🐳 Docker Deployment

### Build and run with Docker:

```bash
# Build image
docker build -t faq-chatbot .

# Run container
docker run -p 8000:8000 --env-file .env faq-chatbot
```

### Using Docker Compose:

```bash
# Start services
docker-compose up --build

# Run in background
docker-compose up -d
```

## 🔒 Security Features

- **CORS Protection**: Configurable origins
- **Rate Limiting**: 60 requests per minute per IP
- **Security Headers**: XSS, CSRF, and content type protection
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Secure error messages without sensitive data

## 📊 Monitoring & Logging

### Structured Logging
All logs are structured JSON for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "logger": "app.services.openai_service",
  "message": "Generated answer for category sales",
  "processing_time": 1.234
}
```

### Health Checks
- `GET /api/health` - Application health status
- Processing time headers on all responses
- Request/response metrics tracking

## 🚀 Production Deployment

### Requirements
- Python 3.11+
- 2GB+ RAM recommended
- OpenAI API access

### Recommended Setup
```bash
# Use a process manager like systemd or supervisor
# Example systemd service:

[Unit]
Description=FAQ Chatbot
After=network.target

[Service]
Type=simple
User=faqbot
WorkingDirectory=/opt/faqbot
Environment=PATH=/opt/faqbot/.venv/bin
ExecStart=/opt/faqbot/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the `/docs` endpoint when running
- **API Reference**: Available at `/docs` and `/redoc`

## 🔄 Changelog

### v1.0.0
- Initial release
- OpenAI function-calling integration
- Three FAQ categories (Sales, Labs, Reports)
- Modern web interface
- Production-ready features 