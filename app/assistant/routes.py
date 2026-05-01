"""
app/assistant/routes.py

Routes for the AI portfolio assistant blueprint.

GET  /assistant        — Renders the chat page (or a "coming soon" placeholder).
POST /assistant/chat   — Accepts a JSON message, returns a grounded AI answer.
"""

from __future__ import annotations

from flask import current_app, jsonify, render_template, request

from app.assistant import assistant_bp, limiter

MAX_MESSAGE_LENGTH = 500


@assistant_bp.get("")
def assistant_page() -> str:
    """Render the assistant chat page."""
    api_key = current_app.config.get("GOOGLE_API_KEY")
    return render_template("assistant/assistant.html", has_api_key=bool(api_key))


@assistant_bp.post("/chat")
@limiter.limit("15 per minute")
@limiter.limit("1500 per day")
def chat():
    """
    Handle a chat message and return a RAG-generated response.

    Request JSON:
        message (str): The user's question (max 500 characters).
        history (list): Prior conversation turns, each with 'role' and 'content'.

    Returns:
        200: {"answer": str, "sources": list[str]}
        400: {"error": str}  — invalid or missing message
        503: {"error": str}  — API key not set or engine unavailable
    """
    api_key = current_app.config.get("GOOGLE_API_KEY")
    if not api_key:
        return (
            jsonify({"error": "Assistant unavailable — API key not configured"}),
            503,
        )

    data = request.get_json(silent=True) or {}
    message: str = (data.get("message") or "").strip()
    history: list[dict] = data.get("history") or []

    if not message:
        return jsonify({"error": "Message is required."}), 400

    if len(message) > MAX_MESSAGE_LENGTH:
        return (
            jsonify({"error": f"Message must be {MAX_MESSAGE_LENGTH} characters or fewer."}),
            400,
        )

    rag_engine = current_app.extensions.get("rag_engine")
    if rag_engine is None:
        return (
            jsonify({"error": "Assistant unavailable — API key not configured"}),
            503,
        )

    try:
        result = rag_engine.chat(message=message, history=history)
        return jsonify(result), 200
    except Exception:
        current_app.logger.exception("RAG engine chat failed.")
        return (
            jsonify({"error": "The assistant encountered an error — please try again."}),
            503,
        )
