"""
config.py

Central configuration for the Flask application.

Key responsibilities:
- Provide environment-based configuration (Development vs Production).
- Define core settings such as SECRET_KEY and DEBUG.
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


class BaseConfig:
    """
    Base configuration shared across environments.
    """

    # Default to a non-empty value so Flask sessions don't break locally.
    # In production, you must set SECRET_KEY as an environment variable.
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-only-change-me")

    # Keep JSON output stable if you ever use jsonify later.
    JSON_SORT_KEYS: bool = False


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


def get_config_class():
    """
    Decide which config class to use based on environment variables.

    Returns:
        type: A configuration class (DevelopmentConfig or ProductionConfig).
    """
    # FLASK_ENV is commonly used. We'll support it for clarity.
    flask_env = os.environ.get("FLASK_ENV", "").strip().lower()

    # FLASK_DEBUG can override behavior when set explicitly.
    flask_debug = os.environ.get("FLASK_DEBUG", "").strip()

    if flask_debug == "1":
        return DevelopmentConfig

    if flask_env == "production":
        return ProductionConfig

    # Default to development for local work.
    return DevelopmentConfig