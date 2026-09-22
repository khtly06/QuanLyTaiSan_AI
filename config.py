"""Central configuration for the Flask application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    _database_url = os.getenv("DATABASE_URL", "")
    if _database_url.startswith("sqlite:///"):
        relative_path = _database_url.replace("sqlite:///", "", 1)
        db_path = Path(relative_path)
        if not db_path.is_absolute():
            db_path = (BASE_DIR / db_path).resolve()
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'database' / 'school_assets.db'}",
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "data" / "documents")
    VECTOR_DB_PATH = str(BASE_DIR / "vector_db")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
