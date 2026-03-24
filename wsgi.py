"""
wsgi.py

WSGI entrypoint for production deployment.

Key responsibilities:
- Expose the Flask application instance for WSGI servers such as Gunicorn.
- Keep deployment entry separate from local development execution.
- Reuse the existing Flask app factory.

Usage:
    gunicorn wsgi:app
"""

from app.app import create_app


app = create_app()  # CI/CD pipeline test