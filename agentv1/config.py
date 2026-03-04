import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / "gitignore" / "environment.env"
COOKIE_CACHE_FILE = BASE_DIR / "cookies.json"
load_dotenv(ENV_PATH)

API_CONFIG = {
    "key": os.getenv("KEY_DEFAULT"),
    "url": os.getenv("AI_URL"),
    "model_chat": "deepseek-chat",
    "model_reasoner": "deepseek-reasoner",
}

BOT_CONFIG = {
    "username": os.getenv("BOT_USERNAME"),
    "access_token": os.getenv("BOT_ACCESS_TOKEN"),
    "room": os.getenv("ROOM_NAME"),
}

SERVER_CONFIG = {
    "http_base": os.getenv("HTTP_BASE") or "https://room.caffeine.ink",
    "login_url": os.getenv("LOGIN_URL") or "https://room.caffeine.ink/api/login",
    "ws_base": "wss://room.caffeine.ink/websocket",
}

CONNECTION_CONFIG = {
    "initial_retry_delay": 1,
    "max_retry_delay": 30,
    "heartbeat_interval": 30,
    "message_buffer_max": 50,
    "memory_interval": 75,
}
