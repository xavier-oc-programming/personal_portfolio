"""
config.py

Central configuration for the Flask application.

Key responsibilities:
- Provide environment-based configuration (Development vs Production).
- Define core settings such as SECRET_KEY, DEBUG, and database path.
- Define Flask-Mail settings for contact form notifications.
- Configure static file caching for better performance.
- Keep configuration logic out of app initialization and routes.

Environment Variables supported:
- FLASK_ENV: "development" or "production" (optional)
- SECRET_KEY: any long random string (required)

Mail-related variables:
- MAIL_SERVER
- MAIL_PORT
- MAIL_USE_TLS
- MAIL_USE_SSL
- MAIL_USERNAME
- MAIL_PASSWORD
- MAIL_DEFAULT_SENDER
- CONTACT_NOTIFICATION_EMAIL

Usage:
    from config import get_config_class
    app.config.from_object(get_config_class())
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "portfolio.db"


def _get_bool_env(var_name: str, default: bool = False) -> bool:
    """
    Read a boolean environment variable using common truthy string values.
    """
    value = os.environ.get(var_name, "").strip().lower()

    if not value:
        return default

    return value in {"1", "true", "yes", "on"}


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

    MAIL_SERVER: str = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS: bool = _get_bool_env("MAIL_USE_TLS", False)
    MAIL_USE_SSL: bool = _get_bool_env("MAIL_USE_SSL", False)
    MAIL_USERNAME: str | None = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD: str | None = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER: str | None = os.environ.get("MAIL_DEFAULT_SENDER")
    CONTACT_NOTIFICATION_EMAIL: str | None = os.environ.get("CONTACT_NOTIFICATION_EMAIL")


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

    Returns:
        type: A configuration class (DevelopmentConfig or ProductionConfig).
    """
    flask_env = os.environ.get("FLASK_ENV", "development").strip().lower()

    if flask_env == "production":
        return ProductionConfig

    return DevelopmentConfig