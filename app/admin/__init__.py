"""
app/admin/__init__.py

Admin blueprint for the portfolio site.
Provides a password-protected interface to manage projects, media, and messages.
"""

from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from app.admin import routes  # noqa: E402, F401
