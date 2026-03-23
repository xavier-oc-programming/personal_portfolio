"""
api/__init__.py

Blueprint registration for the public REST API.

All routes are versioned under /api/v1/.
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

from app.api import routes  # noqa: E402, F401
