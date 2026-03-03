"""
app.py

Flask application entrypoint for the Portfolio Website.

Key responsibilities:
- Create and configure the Flask app instance.
- Load configuration from config.py.
- Define the core navigation routes.
- Provide a single, reliable local run command.
- Inject global template variables shared across all pages.

Run locally (from repo root):
    python app/app.py
"""

from __future__ import annotations

from datetime import datetime

from flask import Flask, render_template
from dotenv import load_dotenv

from config import get_config_class


# Load environment variables from .env (development only)
load_dotenv()


def create_app() -> Flask:
    """
    Application factory.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load config (DevelopmentConfig or ProductionConfig)
    app.config.from_object(get_config_class())

    # ---------------------------------
    # Global Template Context
    # ---------------------------------

    @app.context_processor
    def inject_global_template_vars():
        """
        Inject global variables into all Jinja templates.

        Returns:
            dict: Values available in every template without passing them explicitly.
        """
        return {
            "current_year": datetime.now().year
        }

    # ---------------------------------
    # Core Navigation Routes (1.2)
    # ---------------------------------

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/projects")
    def projects():
        return render_template("projects.html")

    @app.get("/projects/<slug>")
    def project_detail(slug: str):
        # Data logic will be added in Phase 2
        return render_template("project_detail.html", slug=slug)

    @app.get("/contact")
    def contact():
        return render_template("contact.html")

    # ---------------------------------
    # Error Handling
    # ---------------------------------

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()

    # Single source of truth for running locally
    app.run(host="127.0.0.1", port=5000, debug=app.debug)