import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage

# --- Step 1: CONFIGURE LOGGING ---
# This ensures we see every message in the console.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Step 2: VERIFY YOUR CHANNEL SECRET ---
# Hardcode it here for the test. Double-check it's correct from the LINE Dev Console.
# This is the most common point of failure for InvalidSignatureError.
CHANNEL_SECRET = "29cc83f1dfc20dec73718eb97727d286"

if not CHANNEL_SECRET or CHANNEL_SECRET == "PASTE_YOUR_CHANNEL_SECRET_HERE":
    logger.critical("FATAL: CHANNEL_SECRET is not set. Please edit minimal_test.py")
    exit()

# --- Step 3: CREATE THE MINIMAL APP ---
# No middleware, no routers, no config files. Just the bare essentials.
app = FastAPI()
handler = WebhookHandler(CHANNEL_SECRET)

@app.post("/callback")
async def line_webhook(request: Request):
    """
    This is the only endpoint. We put a log right at the top
    to see if the function is ever entered.
    """
    logger.info("--- Minimal test: /callback function has been TRIGGERED! ---") # THIS IS THE KEY LOG
    
    signature = request.headers.get("X-Line-Signature", "")
    body_bytes = await request.body()
    
    try:
        handler.handle(body_bytes.decode('utf-8'), signature)
        logger.info("--- Minimal test: handler.handle() was SUCCESSFUL ---")
    except InvalidSignatureError:
        # If this happens, your Channel Secret is 100% wrong.
        logger.error("!!! Invalid Signature. Please double-check your CHANNEL_SECRET. !!!")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    return {"status": "ok"}

# Add a dummy handler so we can see if an event is processed.
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    logger.info(f"SUCCESS! Message received from user {event.source.user_id}: {event.message.text}")
    # In a real app, you would reply here.
    # line_bot_api.reply_message(...)

# Health check to make sure the server is running
@app.get("/")
def health_check():
    return {"status": "Minimal test server is running!"}

if __name__ == "__main__":
    uvicorn.run(
        "minimal_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
