"""Central configuration for the Flask application."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    _production = os.getenv("FLASK_ENV", "").strip().lower() == "production"
    DEBUG = (
        not _production
        and os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    )
    SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    INITIAL_ADMIN_USERNAME = os.getenv("INITIAL_ADMIN_USERNAME", "").strip()
    INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL", "").strip()
    INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    INITIAL_ADMIN_FULL_NAME = os.getenv("INITIAL_ADMIN_FULL_NAME", "").strip()
    INITIAL_INSPECTOR_USERNAME = os.getenv("INITIAL_INSPECTOR_USERNAME", "").strip()
    INITIAL_INSPECTOR_EMAIL = os.getenv("INITIAL_INSPECTOR_EMAIL", "").strip()
    INITIAL_INSPECTOR_PASSWORD = os.getenv("INITIAL_INSPECTOR_PASSWORD", "")
    INITIAL_INSPECTOR_FULL_NAME = os.getenv("INITIAL_INSPECTOR_FULL_NAME", "").strip()
    INITIAL_STAFF_USERNAME = os.getenv("INITIAL_STAFF_USERNAME", "").strip()
    INITIAL_STAFF_EMAIL = os.getenv("INITIAL_STAFF_EMAIL", "").strip()
    INITIAL_STAFF_PASSWORD = os.getenv("INITIAL_STAFF_PASSWORD", "")
    INITIAL_STAFF_FULL_NAME = os.getenv("INITIAL_STAFF_FULL_NAME", "").strip()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    _database_url = os.getenv("DATABASE_URL", "")
    if _database_url.startswith("sqlite:///"):
        relative_path = _database_url.replace("sqlite:///", "", 1)
        db_path = Path(relative_path)
        if not db_path.is_absolute():
            db_path = (BASE_DIR / db_path).resolve()
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    else:
        SQLALCHEMY_DATABASE_URI = _database_url or (
            f"sqlite:///{BASE_DIR / 'database' / 'school_assets.db'}"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "data" / "documents")
    VECTOR_DB_PATH = str(BASE_DIR / "vector_db")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
    LLM_API_BASE_URL = os.getenv(
        "LLM_API_BASE_URL", "http://localhost:11434/v1/chat/completions"
    )
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    LLM_MAX_PROMPT_CHARS = int(os.getenv("LLM_MAX_PROMPT_CHARS", "12000"))
