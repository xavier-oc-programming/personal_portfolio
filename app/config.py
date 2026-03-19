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

    DATABASE_PATH: Path = DATABASE_FILE
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DATABASE_FILE}"
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