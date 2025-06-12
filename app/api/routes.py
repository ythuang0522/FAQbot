import time
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.models.schemas import ChatRequest, ChatResponse, ErrorResponse, HealthResponse
from app.services.openai_service import OpenAIService
from app.services.line_service import LineService
from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import OpenAIServiceError, FAQNotFoundError
from linebot.v3.exceptions import InvalidSignatureError

# --- Main API Router (with dependencies, etc.) ---
api_router = APIRouter()

router = APIRouter()
templates = Jinja2Templates(directory="frontend/templates")
settings = get_settings()
logger = get_logger(__name__)

# Initialize Line service
line_service = LineService()


@api_router.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Serve the chat interface."""
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "app_name": settings.app_name,
        "app_version": settings.app_version
    })


@api_router.post("/api/chat", response_model=ChatResponse)
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


@api_router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )


@api_router.post("/callback")
async def line_webhook(request: Request):
    """LINE webhook endpoint."""
    logger.info("Line webhook received (in isolated app)")
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    
    try:
        line_service.handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        logger.error("Invalid Line signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Line webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    return {"status": "ok"}

# Export routers for import in main.py
__all__ = ["api_router"] 