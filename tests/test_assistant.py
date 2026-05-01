"""
tests/test_assistant.py

Tests for the AI portfolio assistant blueprint.

All tests mock the RAG engine and Gemini API so they pass in CI
without a real GOOGLE_API_KEY.
"""

import json
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_key_set(app):
    """Temporarily set GOOGLE_API_KEY in app config."""
    app.config["GOOGLE_API_KEY"] = "fake-test-key"
    yield
    app.config["GOOGLE_API_KEY"] = None


@pytest.fixture
def mock_rag_engine(app):
    """Inject a mock RAG engine into app.extensions."""
    mock_engine = MagicMock()
    mock_engine.chat.return_value = {
        "answer": "Xavier is a Python developer based in Madrid.",
        "sources": ["CV", "Projects"],
    }
    app.extensions["rag_engine"] = mock_engine
    yield mock_engine
    app.extensions["rag_engine"] = None


# ---------------------------------------------------------------------------
# GET /assistant
# ---------------------------------------------------------------------------


def test_get_assistant_no_api_key(client):
    """GET /assistant returns 200 and shows coming-soon page when no API key is set."""
    response = client.get("/assistant")
    assert response.status_code == 200
    assert b"Assistant" in response.data


def test_get_assistant_with_api_key(client, api_key_set):
    """GET /assistant returns 200 and shows chat UI when API key is configured."""
    response = client.get("/assistant")
    assert response.status_code == 200
    assert b"assistant" in response.data.lower()


# ---------------------------------------------------------------------------
# POST /assistant/chat — no API key
# ---------------------------------------------------------------------------


def test_post_chat_no_api_key(client):
    """POST /assistant/chat returns 503 when GOOGLE_API_KEY is not set."""
    response = client.post(
        "/assistant/chat",
        data=json.dumps({"message": "hello", "history": []}),
        content_type="application/json",
    )
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data


# ---------------------------------------------------------------------------
# POST /assistant/chat — validation
# ---------------------------------------------------------------------------


def test_post_chat_empty_message(client, api_key_set, mock_rag_engine):
    """POST /assistant/chat returns 400 when message is empty."""
    response = client.post(
        "/assistant/chat",
        data=json.dumps({"message": "", "history": []}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_post_chat_missing_message(client, api_key_set, mock_rag_engine):
    """POST /assistant/chat returns 400 when message key is absent."""
    response = client.post(
        "/assistant/chat",
        data=json.dumps({"history": []}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_post_chat_message_too_long(client, api_key_set, mock_rag_engine):
    """POST /assistant/chat returns 400 when message exceeds 500 characters."""
    response = client.post(
        "/assistant/chat",
        data=json.dumps({"message": "x" * 501, "history": []}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


# ---------------------------------------------------------------------------
# POST /assistant/chat — valid request with mocked RAG
# ---------------------------------------------------------------------------


def test_post_chat_valid(client, api_key_set, mock_rag_engine):
    """POST /assistant/chat returns 200 with correct JSON shape when RAG is mocked."""
    response = client.post(
        "/assistant/chat",
        data=json.dumps({"message": "Tell me about Xavier", "history": []}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_post_chat_passes_history_to_engine(client, api_key_set, mock_rag_engine):
    """POST /assistant/chat forwards conversation history to the RAG engine."""
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]
    client.post(
        "/assistant/chat",
        data=json.dumps({"message": "Follow-up question", "history": history}),
        content_type="application/json",
    )
    call_kwargs = mock_rag_engine.chat.call_args
    assert call_kwargs is not None
    passed_history = call_kwargs.kwargs.get("history") or call_kwargs.args[1]
    assert len(passed_history) == 2


# ---------------------------------------------------------------------------
# POST /assistant/chat — engine failure
# ---------------------------------------------------------------------------


def test_post_chat_engine_failure_returns_503(client, api_key_set, mock_rag_engine):
    """POST /assistant/chat returns 503 when the RAG engine raises an exception."""
    mock_rag_engine.chat.side_effect = RuntimeError("Gemini API error")
    response = client.post(
        "/assistant/chat",
        data=json.dumps({"message": "What are Xavier's skills?", "history": []}),
        content_type="application/json",
    )
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data
