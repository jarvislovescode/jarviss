import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Discord user IDs (right-click a user in Discord > Copy User ID,
# requires Developer Mode enabled in Discord settings)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
RHODEY_ID = int(os.getenv("RHODEY_ID", "0"))

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DB_PATH = os.getenv("DB_PATH", "jarvis.db")

KEEP_ALIVE_PORT = int(os.getenv("PORT", "8080"))
