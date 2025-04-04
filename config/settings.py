import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://postgres:echooo123@localhost:5432/echooo_bot"

# Instagram Credentials
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Instagram URL
INSTAGRAM_URL = "https://www.instagram.com"

# Session Storage Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Root directory
SESSION_STORAGE_DIR = os.path.join(BASE_DIR, "../storage/sessions/instagram")  # Storage folder
SESSION_STORAGE_PATH = os.path.join(SESSION_STORAGE_DIR, "instagram_session.json")  # JSON File

# Playwright headless mode, true/false
HEADLESS_MODE = False