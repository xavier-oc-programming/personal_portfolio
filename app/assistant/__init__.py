"""
app/assistant/__init__.py

AI portfolio assistant blueprint.
Provides a conversational interface that answers recruiter and visitor
questions about Xavier using RAG (Retrieval-Augmented Generation).
"""

from flask import Blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

assistant_bp = Blueprint("assistant", __name__, url_prefix="/assistant")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)

from app.assistant import routes  # noqa: E402, F401
