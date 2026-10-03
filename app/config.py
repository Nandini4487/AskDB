"""
Configuration management for AskDB.
Loads environment variables from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Define base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Load variables from .env file located at root
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Application configuration settings."""
    PROJECT_NAME: str = "AskDB"
    VERSION: str = "0.1.0"
    
    # Gemini AI configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Backend server configuration
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    
    # Storage paths
    DATA_DIR: Path = DATA_DIR
    LOGS_DIR: Path = LOGS_DIR


# Global settings instance
settings = Settings()
