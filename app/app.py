"""
app.py

Flask application entrypoint for the Portfolio Website.

Key responsibilities:
- Create and configure the Flask app instance.
- Load configuration from config.py.
- Define the core navigation routes.
- Provide a single, reliable local run command.
- Inject global template variables shared across all pages.
- Serve project data from an in-memory dataset during Phase 2.

Run locally (from repo root):
    python app/app.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Flask, abort, render_template, request
from dotenv import load_dotenv

from config import get_config_class
from data.projects import get_all_projects, get_project_by_slug


# Load environment variables from .env (development only)
load_dotenv()


ALLOWED_CATEGORIES = {"web", "data", "software"}
ALLOWED_SORTS = {"az", "newest", "oldest"}


def _apply_category_filter(
    projects: list[dict[str, Any]],
    category: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Filter projects by primary_category.

    Parameters:
        projects (list[dict[str, Any]]): Full project list.
        category (str | None): Requested category from querystring.

    Returns:
        tuple[list[dict[str, Any]], str | None]:
            - Filtered project list
            - Normalized active category, or None if invalid/missing
    """
    if not category:
        return projects, None

    normalized_category = category.strip().lower()

    if normalized_category not in ALLOWED_CATEGORIES:
        return projects, None

    filtered_projects = [
        project
        for project in projects
        if str(project.get("primary_category", "")).strip().lower() == normalized_category
    ]

    return filtered_projects, normalized_category


def _apply_sort(
    projects: list[dict[str, Any]],
    sort_key: str | None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Sort projects at the route level.

    Supported sorting:
    - az
    - newest
    - oldest

    Parameters:
        projects (list[dict[str, Any]]): Project list to sort.
        sort_key (str | None): Sort option from querystring.

    Returns:
        tuple[list[dict[str, Any]], str]:
            - Sorted project list
            - Normalized active sort key
    """
    normalized_sort = (sort_key or "az").strip().lower()

    if normalized_sort not in ALLOWED_SORTS:
        normalized_sort = "az"

    if normalized_sort == "az":
        sorted_projects = sorted(
            projects,
            key=lambda project: str(project.get("title", "")).lower()
        )
        return sorted_projects, normalized_sort

    if normalized_sort == "newest":
        sorted_projects = sorted(
            projects,
            key=lambda project: str(project.get("date", "")),
            reverse=True,
        )
        return sorted_projects, normalized_sort

    sorted_projects = sorted(
        projects,
        key=lambda project: str(project.get("date", "")),
    )
    return sorted_projects, normalized_sort


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
    # Core Navigation Routes
    # ---------------------------------

    @app.get("/")
    def home():
        all_projects = get_all_projects()

        featured_projects = [
            project for project in all_projects
            if project.get("featured") is True
        ]

        featured_projects, _ = _apply_sort(featured_projects, "newest")

        return render_template(
            "index.html",
            featured_projects=featured_projects,
        )

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/projects")
    def projects():
        all_projects = get_all_projects()

        category = request.args.get("category")
        sort_key = request.args.get("sort")

        filtered_projects, active_category = _apply_category_filter(all_projects, category)
        sorted_projects, active_sort = _apply_sort(filtered_projects, sort_key)

        # Count projects per category
        category_counts = {
            "all": len(all_projects),
            "web": sum(1 for p in all_projects if p["primary_category"] == "web"),
            "data": sum(1 for p in all_projects if p["primary_category"] == "data"),
            "software": sum(1 for p in all_projects if p["primary_category"] == "software"),
        }

        return render_template(
            "projects.html",
            projects=sorted_projects,
            active_category=active_category,
            active_sort=active_sort,
            category_counts=category_counts
        )
    
    @app.get("/projects/<slug>")
    def project_detail(slug: str):
        project = get_project_by_slug(slug)

        if project is None:
            abort(404)

        return render_template(
            "project_detail.html",
            project=project,
        )

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