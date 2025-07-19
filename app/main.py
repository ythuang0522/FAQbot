from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.api.routes import api_router
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
    description="""
    ## FAQ Chatbot API

    This API provides intelligent FAQ responses using OpenAI's function-calling capabilities.

    ### Features:
    - **Smart Classification**: Automatically routes questions to the appropriate FAQ category
    - **High Accuracy**: Uses GPT-4 for understanding and responding
    - **Fast Response**: Cached responses for common questions
    - **Error Handling**: Comprehensive error handling with detailed feedback
    - **Typing Indicators**: Real-time typing indicators for better UX
    - **Conversation Memory**: Maintains conversation context

    ### Usage:
    1. Send a question to `/api/chat`
    2. Receive categorized response
    3. Follow-up questions maintain conversation context

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
    ],
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

"""
# this will block the line webhook from external access, need fixed webhook url
# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)
"""

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include the main API router in the main app
app.include_router(api_router)

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

settings.print_config()

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