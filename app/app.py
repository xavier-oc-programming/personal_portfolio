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
- Prepare the SQLite database directory/file strategy for Phase 3.
- Initialize SQLAlchemy as the ORM layer for future database integration.
- Create database tables that match the unified project schema.

Run locally (from repo root):
    python app/app.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, abort, render_template, request
from dotenv import load_dotenv

from config import get_config_class
from data.projects import get_all_projects, get_project_by_slug
from models.models import db


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
        category (str | None): Requested category from querystring
            or route-level helper input.

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


def _apply_tag_filter(
    projects: list[dict[str, Any]],
    tag: str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Filter projects by tag.

    Parameters:
        projects (list[dict[str, Any]]): Project list to filter.
        tag (str | None): Requested tag from querystring.

    Returns:
        tuple[list[dict[str, Any]], str | None]:
            - Filtered project list
            - Normalized active tag, or None if missing
    """
    if not tag:
        return projects, None

    normalized_tag = tag.strip().lower()

    if not normalized_tag:
        return projects, None

    filtered_projects = [
        project
        for project in projects
        if normalized_tag in [
            str(project_tag).strip().lower()
            for project_tag in project.get("tags", [])
        ]
    ]

    return filtered_projects, normalized_tag


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


def _get_available_tags(projects: list[dict[str, Any]]) -> list[str]:
    """
    Collect all unique tags from the full project dataset.

    Parameters:
        projects (list[dict[str, Any]]): Full project list.

    Returns:
        list[str]: Alphabetically sorted unique tags.
    """
    tag_set = {
        str(tag).strip().lower()
        for project in projects
        for tag in project.get("tags", [])
        if str(tag).strip()
    }

    return sorted(tag_set)


def _build_projects_page_context(
    category: str | None = None,
    tag: str | None = None,
    sort_key: str | None = None,
) -> dict[str, Any]:
    """
    Build the shared template context for the Projects hub
    and dedicated category pages.

    Parameters:
        category (str | None): Requested category filter.
        tag (str | None): Requested tag filter.
        sort_key (str | None): Requested sort option.

    Returns:
        dict[str, Any]: Context passed into projects.html.
    """
    all_projects = get_all_projects()

    category_filtered_projects, active_category = _apply_category_filter(
        all_projects,
        category,
    )
    tag_filtered_projects, active_tag = _apply_tag_filter(
        category_filtered_projects,
        tag,
    )
    sorted_projects, active_sort = _apply_sort(tag_filtered_projects, sort_key)

    category_counts = {
        "all": len(all_projects),
        "web": sum(
            1 for project in all_projects
            if project.get("primary_category") == "web"
        ),
        "data": sum(
            1 for project in all_projects
            if project.get("primary_category") == "data"
        ),
        "software": sum(
            1 for project in all_projects
            if project.get("primary_category") == "software"
        ),
    }

    available_tags = _get_available_tags(all_projects)

    return {
        "projects": sorted_projects,
        "active_category": active_category,
        "active_tag": active_tag,
        "active_sort": active_sort,
        "category_counts": category_counts,
        "available_tags": available_tags,
    }


def _ensure_database_directory_and_file(app: Flask) -> None:
    """
    Ensure the configured SQLite database directory exists.

    For Phase 3 Section 1.1, we are only formalizing the database
    file strategy. This helper guarantees that the folder exists and
    creates an empty .db file if missing, without creating tables yet.

    Parameters:
        app (Flask): Configured Flask application instance.
    """
    database_path = app.config.get("DATABASE_PATH")

    if not database_path:
        return

    if isinstance(database_path, str):
        database_path = Path(database_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.touch(exist_ok=True)


def create_app() -> Flask:
    """
    Application factory.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load config (DevelopmentConfig or ProductionConfig)
    app.config.from_object(get_config_class())

    # Phase 3 Section 1.1:
    # Ensure the SQLite database directory/file exists.
    _ensure_database_directory_and_file(app)

    # Phase 3 Section 1.2:
    # Initialize SQLAlchemy ORM with the Flask app.
    db.init_app(app)

    # Phase 3 Section 1.3:
    # Create all database tables defined by ORM models.
    with app.app_context():
        db.create_all()

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
        category = request.args.get("category")
        tag = request.args.get("tag")
        sort_key = request.args.get("sort")

        context = _build_projects_page_context(
            category=category,
            tag=tag,
            sort_key=sort_key,
        )

        return render_template("projects.html", **context)

    @app.get("/projects/web")
    def projects_web():
        tag = request.args.get("tag")
        sort_key = request.args.get("sort")

        context = _build_projects_page_context(
            category="web",
            tag=tag,
            sort_key=sort_key,
        )

        return render_template("projects.html", **context)

    @app.get("/projects/data")
    def projects_data():
        tag = request.args.get("tag")
        sort_key = request.args.get("sort")

        context = _build_projects_page_context(
            category="data",
            tag=tag,
            sort_key=sort_key,
        )

        return render_template("projects.html", **context)

    @app.get("/projects/software")
    def projects_software():
        tag = request.args.get("tag")
        sort_key = request.args.get("sort")

        context = _build_projects_page_context(
            category="software",
            tag=tag,
            sort_key=sort_key,
        )

        return render_template("projects.html", **context)

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