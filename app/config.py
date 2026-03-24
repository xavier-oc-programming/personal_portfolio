"""
config.py

Central configuration for the Flask application.

Key responsibilities:
- Provide environment-based configuration (Development vs Production).
- Define core settings such as SECRET_KEY, DEBUG, and database path.
- Define Resend settings for contact form notifications.
- Configure static file caching for better performance.
- Configure production metadata and analytics settings.
- Keep configuration logic out of app initialization and routes.

Environment Variables supported:
- FLASK_ENV: "development" or "production" (optional)
- SECRET_KEY: any long random string (required)
- SITE_URL: public base URL for the portfolio
- SITE_NAME: branding name for SEO and metadata
- DEFAULT_META_DESCRIPTION: default SEO description
- GOOGLE_ANALYTICS_ID: GA4 measurement ID (optional)

Resend-related variables:
- RESEND_API_KEY
- CONTACT_NOTIFICATION_EMAIL

GitHub auto-commit variables (optional — enables auto-committing uploaded media):
- GITHUB_TOKEN: personal access token with repo write permission
- GITHUB_REPO: repository in "owner/repo" format (e.g. xavier-oc-programming/personal_portfolio)

Usage:
    from app.config import get_config_class
    app.config.from_object(get_config_class())
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "portfolio.db"

_DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Supabase (and some other providers) return "postgres://" which SQLAlchemy
# requires as "postgresql://"
if _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)


class BaseConfig:
    """
    Base configuration shared across environments.
    """

    SECRET_KEY: str | None = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set in environment variables.")

    ENV: str = os.environ.get("FLASK_ENV", "development").strip().lower()

    JSON_SORT_KEYS: bool = False
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=30)

    if _DATABASE_URL:
        DATABASE_PATH: Path | None = None
        SQLALCHEMY_DATABASE_URI: str = _DATABASE_URL
        SQLALCHEMY_ENGINE_OPTIONS: dict = {
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 10},
        }
    else:
        DATABASE_PATH = DATABASE_FILE
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_FILE}"
        SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    WTF_CSRF_ENABLED: bool = True

    RESEND_API_KEY: str | None = os.environ.get("RESEND_API_KEY")
    CONTACT_NOTIFICATION_EMAIL: str | None = os.environ.get("CONTACT_NOTIFICATION_EMAIL")

    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "admin")

    SITE_URL: str = os.environ.get("SITE_URL", "http://127.0.0.1:5000").rstrip("/")
    SITE_NAME: str = os.environ.get("SITE_NAME", "Xavier OC | Portfolio")
    DEFAULT_META_DESCRIPTION: str = os.environ.get(
        "DEFAULT_META_DESCRIPTION",
        (
            "Portfolio of Xavier OC — Python Developer specializing in Flask, "
            "data analysis, automation, and structured web application development."
        ),
    )
    GOOGLE_ANALYTICS_ID: str | None = os.environ.get("GOOGLE_ANALYTICS_ID")

    GITHUB_TOKEN: str | None = os.environ.get("GITHUB_TOKEN")
    GITHUB_REPO: str | None = os.environ.get("GITHUB_REPO")

    # Used for JS/CSS cache-busting. Railway injects RAILWAY_GIT_COMMIT_SHA automatically.
    APP_VERSION: str = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "dev")[:8]


class DevelopmentConfig(BaseConfig):
    """
    Local development configuration.
    """

    DEBUG: bool = True


class ProductionConfig(BaseConfig):
    """
    Production configuration.
    """

    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"


def get_config_class():
    """
    Decide which config class to use based on environment variables.
    """
    flask_env = os.environ.get("FLASK_ENV", "development").strip().lower()

    if flask_env == "production":
        return ProductionConfig

    return DevelopmentConfig