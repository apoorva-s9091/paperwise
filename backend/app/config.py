"""
Central place to load environment variables.
Import `settings` anywhere you need a config value instead of
calling os.getenv() directly all over the codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    supabase_url: str = os.environ["SUPABASE_URL"]
    # Service role key bypasses Row Level Security -- only use it in
    # trusted backend code (ingestion), never expose it to a frontend.
    supabase_service_key: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    voyage_api_key: str = os.environ["VOYAGE_API_KEY"]
    groq_api_key: str = os.environ["GROQ_API_KEY"]
    gemini_api_key: str = os.environ["GEMINI_API_KEY"]


settings = Settings()