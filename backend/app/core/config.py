# ============================================================
# MIGRATED during repo restructure (monolith app/ -> 3 services).
# Code is UNCHANGED. Imports below still reference the old `app.*`
# monolith layout and WILL NOT RESOLVE until the owner rewires them.
# TODO(owner): update BASE_DIR usage; MODEL_NAME (Gemini) should read from env, not hardcode.
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    MODEL_NAME: str = "gemini-2.5-flash"
    
settings = Settings()
