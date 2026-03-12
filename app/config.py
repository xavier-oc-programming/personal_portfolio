"""
config.py

Central configuration for the Flask application.

Key responsibilities:
- Provide environment-based configuration (Development vs Production).
- Define core settings such as SECRET_KEY, DEBUG, and database path.
- Keep configuration logic out of app initialization and routes.

Environment Variables supported:
- FLASK_ENV: "development" or "production" (optional)
- FLASK_DEBUG: "1" or "0" (optional)
- SECRET_KEY: any long random string (recommended)

Usage:
    from config import get_config_class
    app.config.from_object(get_config_class())
"""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "portfolio.db"


class BaseConfig:
    """
    Base configuration shared across environments.
    """

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-change-me")
    JSON_SORT_KEYS: bool = False

    DATABASE_PATH: Path = DATABASE_FILE
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DATABASE_FILE}"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    WTF_CSRF_ENABLED: bool = True


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
    flask_env = os.environ.get("FLASK_ENV", "").strip().lower()
    flask_debug = os.environ.get("FLASK_DEBUG", "").strip()

    if flask_debug == "1":
        return DevelopmentConfig

    if flask_env == "production":
        return ProductionConfig

    return DevelopmentConfig