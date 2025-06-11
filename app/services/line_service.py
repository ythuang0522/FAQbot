from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

from app.config import get_settings
from app.services.openai_service import OpenAIService
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

class LineService:
    def __init__(self):
        # Validate Line credentials
        if not settings.line_channel_access_token:
            logger.error("LINE_CHANNEL_ACCESS_TOKEN is not set")
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is required")
        
        if not settings.line_channel_secret:
            logger.error("LINE_CHANNEL_SECRET is not set")
            raise ValueError("LINE_CHANNEL_SECRET is required")
        
        self.configuration = Configuration(
            access_token=settings.line_channel_access_token
        )
        self.handler = WebhookHandler(settings.line_channel_secret)
        self.openai_service = OpenAIService()
        
        # Register message handler - fix the registration
        @self.handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            """Handle incoming Line messages using existing FAQ service."""
            try:
                user_id = event.source.user_id
                question = event.message.text
                
                # Determine conversation ID (use group_id if in group, otherwise user_id)
                conversation_id = user_id
                if event.source.type == "group":
                    conversation_id = event.source.group_id
                elif event.source.type == "room":
                    conversation_id = event.source.room_id
                
                logger.info(f"Processing LINE message from {user_id}: {question}")
                
                # Use a simpler approach - run in a new thread with its own event loop
                import asyncio
                import threading
                
                result_container = {"result": None, "error": None}
                
                def async_worker():
                    try:
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Run the async function
                        result = loop.run_until_complete(
                            self.openai_service.get_faq_answer(
                                question=question,
                                conversation_id=conversation_id
                            )
                        )
                        result_container["result"] = result
                        
                    except Exception as e:
                        result_container["error"] = e
                    finally:
                        loop.close()
                
                # Run async work in separate thread
                thread = threading.Thread(target=async_worker)
                thread.start()
                thread.join(timeout=30)  # 30 second timeout
                
                if thread.is_alive():
                    raise TimeoutError("OpenAI processing timed out")
                
                if result_container["error"]:
                    raise result_container["error"]
                
                if not result_container["result"]:
                    raise RuntimeError("No result returned from OpenAI service")
                
                result = result_container["result"]
                response_text = result["answer"]
                
                # Send LINE reply
                with ApiClient(self.configuration) as api_client:
                    messaging_api = MessagingApi(api_client)
                    messaging_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=response_text)]
                        )
                    )
                
                logger.info(f"LINE message processed successfully for user: {user_id}")
                
            except Exception as e:
                logger.error(f"Error processing LINE message: {e}")
                try:
                    with ApiClient(self.configuration) as api_client:
                        messaging_api = MessagingApi(api_client)
                        error_message = "抱歉，處理您的問題時發生錯誤，請稍後再試。"
                        messaging_api.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,
                                messages=[TextMessage(text=error_message)]
                            )
                        )
                except Exception as reply_error:
                    logger.error(f"Failed to send error message: {reply_error}")
        
        logger.info("LineService initialized successfully") 