import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.environ["TG_API_ID"])
    API_HASH = os.environ["TG_API_HASH"]
    SESSION = os.getenv("TG_SESSION", "")
    NOTIFY_TARGET = os.getenv("TG_NOTIFY_TARGET", "me")
    CHANNELS = [c.strip() for c in os.getenv("TG_CHANNELS", "").split(",") if c.strip()]
    ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
    MIN_SCORE = int(os.getenv("MIN_SCORE", "7"))
    MIN_TEXT_LENGTH = int(os.getenv("MIN_TEXT_LENGTH", "80"))
