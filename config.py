import os

class Config:
    TOKEN = os.getenv("TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")
    WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "http://postimg.cc/0MfGMb0Q")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")
    HEARTBEAT_INTERVAL = 60
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", 8080))
