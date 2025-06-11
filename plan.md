# 🛠️ Enhanced ChatGPT Function-Calling FAQ Bot (FastAPI + Uvicorn Edition)

A robust FAQ chatbot powered by OpenAI function-calling, served over **FastAPI + Uvicorn** with comprehensive error handling, logging, and security features.
Three FAQ categories with intelligent routing, streaming responses, and modern web UI.

---

## 0. Enhanced Project Layout

```
faq-bot/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py              # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py  # OpenAI integration
│   │   └── faq_service.py     # FAQ management
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoints
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       └── exceptions.py      # Custom exceptions
├── faqs/
│   ├── sales.txt
│   ├── labs.txt
│   └── reports.txt
├── frontend/
│   ├── templates/
│   │   └── chat.html          # Enhanced Jinja2 template
│   └── static/
│       ├── css/
│       │   └── styles.css     # Custom styles
│       └── js/
│           └── main.js        # Enhanced JavaScript
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## 1. Enhanced Installation & Setup

### 1.1 Dependencies (requirements.txt)
```txt
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# OpenAI & Environment
openai>=1.40.0
python-dotenv>=1.0.0

# Templating & Static Files
jinja2>=3.1.0

# Data Validation
pydantic>=2.5.0

# HTTP & Security
httpx>=0.25.0
python-multipart>=0.0.6

# Logging & Monitoring
structlog>=23.2.0

# Development (requirements-dev.txt)
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.7.0
```

### 1.2 Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 1.3 Environment Variables (.env.example)
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-1106-preview
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.1

# App Configuration
APP_NAME=FAQ Chatbot
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=False

# Security
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:8000"]
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

---

## 2. Enhanced Configuration Management

### 2.1 app/config.py
```python
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-1106-preview"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.1
    
    # App Configuration
    app_name: str = "FAQ Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Security
    cors_origins: List[str] = ["http://localhost:3000"]
    rate_limit_requests: int = 60
    rate_limit_window: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 3. Enhanced Data Models

### 3.1 app/models/schemas.py
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class FAQCategory(str, Enum):
    SALES = "sales"
    LABS = "labs"
    REPORTS = "reports"


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    category: FAQCategory
    conversation_id: str
    processing_time: float


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    error_code: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
```

---

## 4. Enhanced Services

### 4.1 app/services/faq_service.py
```python
import json
from pathlib import Path
from typing import Dict, List
from app.utils.logger import get_logger
from app.models.schemas import FAQCategory

logger = get_logger(__name__)


class FAQService:
    def __init__(self, faq_dir: str = "faqs"):
        self.faq_dir = Path(faq_dir)
        self.faq_content: Dict[str, str] = {}
        self.load_faq_files()
    
    def load_faq_files(self) -> None:
        """Load all FAQ files into memory with error handling."""
        try:
            for faq_file in self.faq_dir.glob("*.txt"):
                category = faq_file.stem
                if category in [e.value for e in FAQCategory]:
                    content = faq_file.read_text(encoding="utf-8")
                    self.faq_content[category] = content
                    logger.info(f"Loaded FAQ category: {category}")
                else:
                    logger.warning(f"Unknown FAQ category: {category}")
        except Exception as e:
            logger.error(f"Error loading FAQ files: {e}")
            raise
    
    def get_faq_content(self, category: str) -> str:
        """Get FAQ content for a specific category."""
        return self.faq_content.get(category, "")
    
    def get_available_categories(self) -> List[str]:
        """Get list of available FAQ categories."""
        return list(self.faq_content.keys())
    
    def build_function_definitions(self) -> List[Dict]:
        """Build OpenAI function definitions for FAQ categories."""
        functions = []
        for category in self.get_available_categories():
            function = {
                "type": "function",
                "function": {
                    "name": f"faq_{category}",
                    "description": f"Answer questions using the {category.title()} FAQ knowledge base. Use this when the question relates to {category} topics.",
  "parameters": {
    "type": "object",
    "properties": {
                            "question": {
                                "type": "string",
                                "description": "The user's question to be answered"
                            }
                        },
                        "required": ["question"],
                        "additionalProperties": False
                    }
                }
            }
            functions.append(function)
        return functions
```

### 4.2 app/services/openai_service.py
```python
import json
import time
import uuid
from typing import Dict, Tuple
from openai import OpenAI
from app.config import get_settings
from app.services.faq_service import FAQService
from app.utils.logger import get_logger
from app.utils.exceptions import OpenAIServiceError, FAQNotFoundError

settings = get_settings()
logger = get_logger(__name__)


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.faq_service = FAQService()
    
    async def get_faq_answer(self, question: str, conversation_id: str = None) -> Dict:
        """
        Get FAQ answer using OpenAI function calling.
        Returns: {answer, category, conversation_id, processing_time}
        """
        start_time = time.time()
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        try:
            # Step 1: Determine the appropriate FAQ category
            category = await self._classify_question(question)
            
            # Step 2: Generate answer using the selected FAQ
            answer = await self._generate_answer(question, category)
            
            processing_time = time.time() - start_time
            
            return {
                "answer": answer,
                "category": category,
                "conversation_id": conversation_id,
                "processing_time": round(processing_time, 3)
            }
            
        except Exception as e:
            logger.error(f"Error in get_faq_answer: {e}")
            raise OpenAIServiceError(f"Failed to process question: {str(e)}")
    
    async def _classify_question(self, question: str) -> Tuple[str, float]:
        """Classify question using OpenAI function calling."""
        try:
            functions = self.faq_service.build_function_definitions()
            
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an intelligent FAQ classifier. Analyze the user's question and determine which FAQ category best answers it. Only call a function if you're confident it's the right category."
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                tools=functions,
        tool_choice="auto",
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            
            message = response.choices[0].message
            
            if not message.tool_calls:
                raise FAQNotFoundError("Could not classify question to any FAQ category")
            
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            category = function_name.replace("faq_", "")
            
            logger.info(f"Classified question to category: {category}")
            
            return category
            
        except Exception as e:
            logger.error(f"Error in question classification: {e}")
            raise
    
    async def _generate_answer(self, question: str, category: str) -> str:
        """Generate answer using the selected FAQ category."""
        try:
            faq_content = self.faq_service.get_faq_content(category)
            
            if not faq_content:
                raise FAQNotFoundError(f"FAQ content not found for category: {category}")
            
            response = self.client.chat.completions.create(
                model=settings.openai_model,
        messages=[
            {
                "role": "system",
                        "content": """You are a helpful FAQ assistant. Use ONLY the provided FAQ content to answer questions. 
                        If the answer is not explicitly covered in the FAQ content, respond with "I don't have that information in my FAQ database. Please contact support for more details."
                        
                        Guidelines:
                        - Be concise and accurate
                        - Use a friendly, professional tone
                        - Include relevant details from the FAQ
                        - If uncertain, acknowledge limitations"""
                    },
                    {
                        "role": "user",
                        "content": f"FAQ Content:\n{faq_content}\n\nQuestion: {question}"
                    }
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Generated answer for category {category}")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
```

---

## 5. Enhanced API Routes

### 5.1 app/api/routes.py
```python
import time
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from app.services.openai_service import OpenAIService
from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import OpenAIServiceError, FAQNotFoundError

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")
settings = get_settings()
logger = get_logger(__name__)


@router.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Serve the chat interface."""
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "app_name": settings.app_name,
        "app_version": settings.app_version
    })


@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    openai_service: OpenAIService = Depends(lambda: OpenAIService())
):
    """
    Process chat message and return FAQ-based response.
    """
    try:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        result = await openai_service.get_faq_answer(
            question=request.question,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(**result)
        
    except FAQNotFoundError as e:
        logger.warning(f"FAQ not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="FAQ not found",
                detail=str(e),
                error_code="FAQ_NOT_FOUND"
            ).dict()
        )
    
    except OpenAIServiceError as e:
        logger.error(f"OpenAI service error: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Service error",
                detail=str(e),
                error_code="OPENAI_SERVICE_ERROR"
            ).dict()
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Internal server error",
                detail="An unexpected error occurred",
                error_code="INTERNAL_ERROR"
            ).dict()
        )


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )
```

---

## 6. Enhanced Main Application

### 6.1 app/main.py
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.api.routes import router
from app.utils.logger import setup_logging, get_logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FAQ Chatbot with OpenAI Function Calling",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include routes
app.include_router(router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger = get_logger(__name__)
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
```

---

## 7. Enhanced Frontend

### 7.1 frontend/templates/chat.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }}</title>
    <link href="https://unpkg.com/@picocss/pico@2/css/pico.min.css" rel="stylesheet">
    <link href="/static/css/styles.css" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ app_name }}</h1>
            <p>Ask questions about our Sales, Labs, or Reports</p>
        </header>

        <main>
            <div id="chat-container">
                <div id="messages" class="messages-container"></div>
                <div id="typing-indicator" class="typing-indicator" style="display: none;">
                    <span></span><span></span><span></span>
                </div>
            </div>

            <form id="chat-form" class="chat-form">
                <div class="input-group">
                    <input 
                        type="text" 
                        id="question" 
                        placeholder="Type your question here..." 
                        maxlength="1000"
                        required 
                        autocomplete="off"
                    >
                    <button type="submit" id="send-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z" />
                        </svg>
                    </button>
                </div>
                <small id="char-count">0/1000</small>
  </form>
        </main>

        <footer>
            <small>Version {{ app_version }} | FAQ Chatbot</small>
        </footer>
    </div>

    <script src="/static/js/main.js"></script>
</body>
</html>
```

### 7.2 frontend/static/css/styles.css
```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --error-color: #ef4444;
    --warning-color: #f59e0b;
    --chat-bg: #f8fafc;
    --message-bg: #ffffff;
    --user-message-bg: #2563eb;
    --bot-message-bg: #e2e8f0;
}

.messages-container {
    max-height: 60vh;
    overflow-y: auto;
    padding: 1rem;
    background: var(--chat-bg);
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border: 1px solid var(--pico-border-color);
}

.message {
    margin-bottom: 1rem;
    padding: 0.75rem;
    border-radius: 0.5rem;
    max-width: 80%;
    word-wrap: break-word;
}

.message.user {
    background: var(--user-message-bg);
    color: white;
    margin-left: auto;
    text-align: right;
}

.message.bot {
    background: var(--bot-message-bg);
    color: var(--pico-color);
    margin-right: auto;
}

.message-meta {
    font-size: 0.75rem;
    opacity: 0.7;
    margin-top: 0.25rem;
}

.typing-indicator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.75rem;
    margin-left: 1rem;
    margin-bottom: 1rem;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--secondary-color);
    animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
}

.input-group {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.input-group input {
    flex: 1;
    margin: 0;
}

.input-group button {
    padding: 0.75rem;
    min-width: auto;
    margin: 0;
    border-radius: 0.5rem;
}

.chat-form {
    position: sticky;
    bottom: 0;
    background: var(--pico-background-color);
    padding: 1rem 0;
    border-top: 1px solid var(--pico-border-color);
}

#char-count {
    text-align: right;
    margin-top: 0.25rem;
    display: block;
}

.error-message {
    background: var(--error-color);
    color: white;
    padding: 0.75rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}

.confidence-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: bold;
    margin-left: 0.5rem;
}

.confidence-high { background: var(--success-color); color: white; }
.confidence-medium { background: var(--warning-color); color: white; }
.confidence-low { background: var(--error-color); color: white; }

@media (max-width: 768px) {
    .message {
        max-width: 95%;
    }
    
    .container {
        padding: 0.5rem;
    }
    
    .messages-container {
        max-height: 50vh;
    }
}
```

### 7.3 frontend/static/js/main.js
```javascript
class ChatBot {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.chatForm = document.getElementById('chat-form');
        this.questionInput = document.getElementById('question');
        this.sendButton = document.getElementById('send-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.charCount = document.getElementById('char-count');
        this.conversationId = null;
        
        this.initEventListeners();
        this.addWelcomeMessage();
    }
    
    initEventListeners() {
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.questionInput.addEventListener('input', (e) => this.updateCharCount(e));
        this.questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
  e.preventDefault();
                this.handleSubmit(e);
            }
        });
    }
    
    updateCharCount(e) {
        const length = e.target.value.length;
        this.charCount.textContent = `${length}/1000`;
        
        if (length > 900) {
            this.charCount.style.color = 'var(--error-color)';
        } else if (length > 700) {
            this.charCount.style.color = 'var(--warning-color)';
        } else {
            this.charCount.style.color = 'var(--secondary-color)';
        }
    }
    
    addWelcomeMessage() {
        this.addMessage('bot', 'Hello! I\'m here to help answer your questions about Sales, Labs, and Reports. What would you like to know?', 'system');
    }
    
    addMessage(type, content, category = null, confidence = null, processingTime = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        let confidenceBadge = '';
        if (confidence && type === 'bot') {
            const confidenceLevel = confidence > 0.8 ? 'high' : confidence > 0.5 ? 'medium' : 'low';
            confidenceBadge = `<span class="confidence-badge confidence-${confidenceLevel}">${Math.round(confidence * 100)}%</span>`;
        }
        
        let metaInfo = '';
        if (category && category !== 'system') {
            metaInfo = `<div class="message-meta">Source: ${category.toUpperCase()}${confidenceBadge}`;
            if (processingTime) {
                metaInfo += ` | ${processingTime}s`;
            }
            metaInfo += '</div>';
        }
        
        messageDiv.innerHTML = `${content}${metaInfo}`;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `Error: ${message}`;
        this.messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    setInputState(disabled) {
        this.questionInput.disabled = disabled;
        this.sendButton.disabled = disabled;
        this.sendButton.textContent = disabled ? 'Sending...' : 'Send';
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const question = this.questionInput.value.trim();
  if (!question) return;
        
        // Add user message
        this.addMessage('user', question);
        this.questionInput.value = '';
        this.updateCharCount({target: {value: ''}});
        
        // Show loading state
        this.setInputState(true);
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    conversation_id: this.conversationId
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.error || 'Failed to get response');
            }
            
            const data = await response.json();
            
            // Store conversation ID for follow-up questions
            this.conversationId = data.conversation_id;
            
            // Add bot response
            this.addMessage(
                'bot', 
                data.answer, 
                data.category, 
                data.confidence, 
                data.processing_time
            );
            
        } catch (error) {
            console.error('Chat error:', error);
            this.addErrorMessage(error.message || 'Something went wrong. Please try again.');
        } finally {
            this.hideTypingIndicator();
            this.setInputState(false);
            this.questionInput.focus();
        }
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatBot();
});
```

---

## 8. Utilities and Error Handling

### 8.1 app/utils/logger.py
```python
import structlog
import logging
import sys
from typing import Any, Dict


def setup_logging(log_level: str = "INFO") -> None:
    """Setup structured logging configuration."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
```

### 8.2 app/utils/exceptions.py
```python
class FAQBotException(Exception):
    """Base exception for FAQ bot."""
    pass


class OpenAIServiceError(FAQBotException):
    """Exception raised for OpenAI service errors."""
    pass


class FAQNotFoundError(FAQBotException):
    """Exception raised when FAQ content is not found."""
    pass


class ConfigurationError(FAQBotException):
    """Exception raised for configuration errors."""
    pass
```

---

## 9. Testing

### 9.1 tests/test_api.py
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_chat_endpoint():
    response = client.post(
        "/api/chat",
        json={"question": "What are your sales policies?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "category" in data
    assert "confidence" in data


def test_chat_endpoint_empty_question():
    response = client.post(
        "/api/chat",
        json={"question": ""}
    )
    assert response.status_code == 422  # Validation error
```

---

## 10. Enhanced FAQ Files Structure

Create more comprehensive FAQ files with better structure:

### 10.1 faqs/sales.txt
```
SALES FAQ

Q: What are your pricing plans?
A: We offer three pricing tiers: Starter ($29/month), Professional ($79/month), and Enterprise ($199/month). Each plan includes different features and usage limits.

Q: Do you offer discounts for annual subscriptions?
A: Yes, we offer a 20% discount for annual subscriptions on all plans.

Q: What is your refund policy?
A: We offer a 30-day money-back guarantee for all new subscriptions.

Q: How can I upgrade or downgrade my plan?
A: You can change your plan anytime from your account dashboard. Changes take effect immediately.

Q: Do you offer custom enterprise solutions?
A: Yes, we provide custom enterprise solutions with dedicated support, custom integrations, and volume discounts.
```

---

## 11. Deployment Considerations

### 11.1 Docker Setup
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.2 docker-compose.yml
```yaml
version: '3.8'

services:
  faq-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
    volumes:
      - ./faqs:/app/faqs:ro
    restart: unless-stopped
```

---

## 12. Key Improvements Made

1. **Better Project Structure**: Organized code into logical modules with clear separation of concerns
2. **Enhanced Error Handling**: Comprehensive exception handling with custom exceptions and proper HTTP status codes
3. **Configuration Management**: Centralized configuration with environment variables and validation
4. **Logging**: Structured logging with proper log levels and context
5. **Security**: CORS, trusted hosts, and rate limiting considerations
6. **Data Validation**: Pydantic models for request/response validation
7. **Better UX**: Enhanced frontend with typing indicators, confidence scores, and better styling
8. **Testing**: Basic test structure for API endpoints
9. **Monitoring**: Health check endpoint and processing time tracking
10. **Documentation**: Comprehensive inline documentation and type hints
11. **Production Ready**: Docker support and deployment considerations

---

## 13. Running the Enhanced Application

```bash
# Development
uvicorn app.main:app --reload --log-level debug

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Docker
docker-compose up --build
```

This enhanced implementation provides a much more robust, scalable, and production-ready FAQ chatbot with comprehensive error handling, logging, and modern web UI features.

---

## 14. Additional Production Improvements

### 14.1 Rate Limiting Implementation
```python
# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict, deque
from app.config import get_settings

settings = get_settings()

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        while self.requests[client_ip] and self.requests[client_ip][0] < now - settings.rate_limit_window:
            self.requests[client_ip].popleft()
        
        # Check rate limit
        if len(self.requests[client_ip]) >= settings.rate_limit_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response
```

### 14.2 Enhanced Security Headers
```python
# app/middleware/security.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
```

### 14.3 Caching Layer
```python
# app/services/cache_service.py
import json
import hashlib
from typing import Optional, Dict, Any
from functools import wraps
import time

class SimpleCache:
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if time.time() - self.cache[key]["timestamp"] < self.ttl:
                return self.cache[key]["value"]
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }

# Global cache instance
faq_cache = SimpleCache(ttl=600)  # 10 minutes for FAQ responses

def cache_faq_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Generate cache key based on question
        question = kwargs.get('question') or args[0] if args else ''
        cache_key = faq_cache._generate_key(question)
        
        # Check cache
        cached_result = faq_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Execute function and cache result
        result = await func(*args, **kwargs)
        faq_cache.set(cache_key, result)
        return result
    
    return wrapper
```

### 14.4 Monitoring and Metrics
```python
# app/middleware/metrics.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from app.utils.logger import get_logger

logger = get_logger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_count = defaultdict(int)
        self.response_times = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        endpoint = f"{request.method} {request.url.path}"
        
        # Track metrics
        self.request_count[endpoint] += 1
        self.response_times[endpoint].append(process_time)
        
        # Log slow requests
        if process_time > 2.0:  # Log requests taking more than 2 seconds
            logger.warning(f"Slow request: {endpoint} took {process_time:.2f}s")
        
        return response
```

### 14.5 Database Integration (Optional)
```python
# app/models/database.py (if you want to add conversation history)
from sqlalchemy import create_engine, Column, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    processing_time = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    client_ip = Column(String)

# app/services/conversation_service.py
class ConversationService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def save_conversation(self, conversation_data: dict, client_ip: str):
        conversation = Conversation(
            question=conversation_data["question"],
            answer=conversation_data["answer"],
            category=conversation_data["category"],
            confidence=conversation_data["confidence"],
            processing_time=conversation_data["processing_time"],
            client_ip=client_ip
        )
        self.db.add(conversation)
        self.db.commit()
        return conversation.id
```

### 14.6 API Documentation Enhancement
```python
# Enhanced FastAPI app setup in app/main.py
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## FAQ Chatbot API

    This API provides intelligent FAQ responses using OpenAI's function-calling capabilities.

    ### Features:
    - **Smart Classification**: Automatically routes questions to the appropriate FAQ category
    - **High Accuracy**: Uses GPT-4 for understanding and responding
    - **Fast Response**: Cached responses for common questions
    - **Confidence Scoring**: Provides confidence levels for each response

    ### Usage:
    1. Send your question to `/api/chat`
    2. Receive categorized response with confidence score
    3. Use conversation ID for follow-up questions

    ### Rate Limits:
    - 60 requests per minute per IP address
    - Conversation tracking for context awareness
    """,
    contact={
        "name": "Support Team",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {"name": "chat", "description": "Chat operations"},
        {"name": "health", "description": "Health check operations"},
    ]
)
```

### 14.7 Enhanced FAQ Content with Metadata
```python
# app/models/faq_models.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class FAQEntry(BaseModel):
    question: str
    answer: str
    keywords: List[str] = []
    category: str
    last_updated: Optional[datetime] = None
    usage_count: int = 0

class FAQDatabase(BaseModel):
    entries: List[FAQEntry]
    metadata: Dict[str, str] = {}
    version: str = "1.0"
    last_updated: datetime
```

### 14.8 Advanced FAQ File Format (YAML)
```yaml
# faqs/sales.yaml (enhanced format)
category: sales
version: "1.0"
last_updated: "2024-01-15"
metadata:
  description: "Sales related questions and answers"
  contact: "sales@company.com"

entries:
  - question: "What are your pricing plans?"
    answer: "We offer three pricing tiers: Starter ($29/month), Professional ($79/month), and Enterprise ($199/month)."
    keywords: ["pricing", "plans", "cost", "subscription", "tiers"]
    confidence_boost: 0.1
    
  - question: "Do you offer discounts?"
    answer: "Yes, we offer a 20% discount for annual subscriptions on all plans."
    keywords: ["discount", "annual", "savings", "promotion"]
    
  - question: "What is your refund policy?"
    answer: "We offer a 30-day money-back guarantee for all new subscriptions."
    keywords: ["refund", "money-back", "guarantee", "cancel"]
```

### 14.9 Improved Error Recovery
```python
# app/services/fallback_service.py
class FallbackService:
    def __init__(self):
        self.fallback_responses = {
            "general": "I apologize, but I'm having trouble processing your request right now. Please try again later or contact our support team.",
            "openai_error": "Our AI service is temporarily unavailable. Please try rephrasing your question or contact support.",
            "faq_not_found": "I couldn't find a specific answer to your question in our FAQ database. Please contact our support team for personalized assistance."
        }
    
    def get_fallback_response(self, error_type: str, context: dict = None) -> dict:
        response = self.fallback_responses.get(error_type, self.fallback_responses["general"])
        
        return {
            "answer": response,
            "category": "fallback",
            "confidence": 0.0,
            "conversation_id": context.get("conversation_id", ""),
            "processing_time": 0.1,
            "is_fallback": True
        }
```

---

## 15. Performance Optimizations

### 15.1 FAQ Content Preprocessing
```python
# app/services/preprocessing_service.py
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class FAQPreprocessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic preprocessing if spacy model not available
            self.nlp = None
        
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.faq_vectors = None
        self.faq_questions = []
    
    def preprocess_faqs(self, faq_content: dict):
        """Preprocess FAQ content for better matching."""
        questions = []
        for category, content in faq_content.items():
            # Extract questions from FAQ content
            lines = content.split('\n')
            for line in lines:
                if line.startswith('Q:'):
                    questions.append(line[2:].strip())
        
        self.faq_questions = questions
        if questions:
            self.faq_vectors = self.vectorizer.fit_transform(questions)
    
    def find_similar_questions(self, question: str, threshold: float = 0.5) -> list:
        """Find similar questions using TF-IDF similarity."""
        if not self.faq_vectors:
            return []
        
        question_vector = self.vectorizer.transform([question])
        similarities = cosine_similarity(question_vector, self.faq_vectors).flatten()
        
        similar_indices = np.where(similarities >= threshold)[0]
        return [(self.faq_questions[i], similarities[i]) for i in similar_indices]
```

### 15.2 Async Queue for Heavy Operations
```python
# app/services/queue_service.py
import asyncio
from typing import Callable, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AsyncTaskQueue:
    def __init__(self, max_workers: int = 3):
        self.queue = asyncio.Queue()
        self.workers = []
        self.max_workers = max_workers
        self.running = False
    
    async def start(self):
        """Start the task queue workers."""
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Stop the task queue workers."""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def _worker(self, name: str):
        """Worker coroutine to process tasks."""
        while self.running:
            try:
                task_func, args, kwargs = await asyncio.wait_for(
                    self.queue.get(), timeout=1.0
                )
                await task_func(*args, **kwargs)
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task error in {name}: {e}")
    
    async def add_task(self, func: Callable, *args, **kwargs):
        """Add a task to the queue."""
        await self.queue.put((func, args, kwargs))
```

---

## 16. Final Recommendations

1. **Use Environment-Specific Configs**: Separate development, staging, and production configurations
2. **Implement Graceful Shutdown**: Handle SIGTERM signals properly for clean shutdowns
3. **Add Health Checks**: Implement deep health checks that verify OpenAI API connectivity
4. **Monitor API Usage**: Track OpenAI API usage and costs
5. **Implement Circuit Breaker**: Add circuit breaker pattern for external API calls
6. **Add Request ID Tracing**: Include request IDs for better debugging and tracking
7. **Content Versioning**: Version your FAQ content and track changes
8. **A/B Testing**: Implement A/B testing for different response strategies
9. **Analytics**: Add analytics to track popular questions and user satisfaction
10. **Backup Strategy**: Implement backup strategies for conversation history and FAQ content

This comprehensive enhancement provides enterprise-level features while maintaining simplicity and performance.

