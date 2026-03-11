"""
app.py

Flask application entrypoint for the Portfolio Website.

Key responsibilities:
- Create and configure the Flask app instance.
- Load configuration from config.py.
- Define the core navigation routes.
- Provide a single, reliable local run command.
- Inject global template variables shared across all pages.
- Serve project data from the database during Phase 3.
- Prepare the SQLite database directory/file strategy.
- Initialize SQLAlchemy as the ORM layer.
- Create database tables that match the unified project schema.

Run locally (from repo root):
    python app/app.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, abort, render_template, request

from config import get_config_class
from models.models import Project, db


# Load environment variables from .env (development only)
load_dotenv()


ALLOWED_CATEGORIES = {"web", "data", "software"}
ALLOWED_SORTS = {"az", "newest", "oldest"}


def _normalize_category(category: str | None) -> str | None:
    """
    Normalize and validate a category value.

    Parameters:
        category (str | None): Raw category input.

    Returns:
        str | None: Normalized category if valid, otherwise None.
    """
    if not category:
        return None

    normalized_category = category.strip().lower()

    if normalized_category not in ALLOWED_CATEGORIES:
        return None

    return normalized_category


def _normalize_tag(tag: str | None) -> str | None:
    """
    Normalize a tag value.

    Parameters:
        tag (str | None): Raw tag input.

    Returns:
        str | None: Normalized tag or None if empty.
    """
    if not tag:
        return None

    normalized_tag = tag.strip().lower()

    if not normalized_tag:
        return None

    return normalized_tag


def _normalize_sort(sort_key: str | None) -> str:
    """
    Normalize and validate a sort key.

    Parameters:
        sort_key (str | None): Raw sort input.

    Returns:
        str: One of the allowed sort options.
    """
    normalized_sort = (sort_key or "az").strip().lower()

    if normalized_sort not in ALLOWED_SORTS:
        return "az"

    return normalized_sort


def _apply_database_filters(
    category: str | None = None,
    tag: str | None = None,
):
    """
    Build the base database query for projects.

    Parameters:
        category (str | None): Optional project category filter.
        tag (str | None): Optional tag filter.

    Returns:
        BaseQuery: Filtered SQLAlchemy query object.
    """
    normalized_category = _normalize_category(category)
    normalized_tag = _normalize_tag(tag)

    query = Project.query

    if normalized_category:
        query = query.filter(Project.primary_category == normalized_category)

    if normalized_tag:
        # tags are stored as JSON text like:
        # ["flask", "jinja", "bootstrap"]
        #
        # Matching with %"tag"% helps match the full JSON string value
        # instead of a loose substring inside another word.
        query = query.filter(Project.tags_json.ilike(f'%"{normalized_tag}"%'))

    return query


def _apply_sort(query, sort_key: str | None):
    """
    Apply sorting to a SQLAlchemy query.

    Supported sorting:
    - az
    - newest
    - oldest

    Parameters:
        query: SQLAlchemy query object.
        sort_key (str | None): Sort option from querystring.

    Returns:
        tuple:
            - Sorted SQLAlchemy query object
            - Normalized active sort key
    """
    normalized_sort = _normalize_sort(sort_key)

    if normalized_sort == "az":
        return query.order_by(Project.title.asc()), normalized_sort

    if normalized_sort == "newest":
        return query.order_by(Project.date.desc(), Project.title.asc()), normalized_sort

    return query.order_by(Project.date.asc(), Project.title.asc()), normalized_sort


def _get_available_tags() -> list[str]:
    """
    Collect all unique tags from all projects stored in the database.

    Returns:
        list[str]: Alphabetically sorted unique tags.
    """
    tag_set: set[str] = set()

    all_projects = Project.query.all()

    for project in all_projects:
        for tag in project.tags:
            normalized_tag = str(tag).strip().lower()

            if normalized_tag:
                tag_set.add(normalized_tag)

    return sorted(tag_set)


def _get_category_counts() -> dict[str, int]:
    """
    Compute total counts for each category.

    Returns:
        dict[str, int]: Counts for all/web/data/software.
    """
    return {
        "all": Project.query.count(),
        "web": Project.query.filter_by(primary_category="web").count(),
        "data": Project.query.filter_by(primary_category="data").count(),
        "software": Project.query.filter_by(primary_category="software").count(),
    }


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
    active_category = _normalize_category(category)
    active_tag = _normalize_tag(tag)

    query = _apply_database_filters(
        category=active_category,
        tag=active_tag,
    )

    sorted_query, active_sort = _apply_sort(query, sort_key)
    projects = sorted_query.all()

    return {
        "projects": projects,
        "active_category": active_category,
        "active_tag": active_tag,
        "active_sort": active_sort,
        "category_counts": _get_category_counts(),
        "available_tags": _get_available_tags(),
    }


def _ensure_database_directory_and_file(app: Flask) -> None:
    """
    Ensure the configured SQLite database directory exists.

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

    # Ensure the SQLite database directory/file exists.
    _ensure_database_directory_and_file(app)

    # Initialize SQLAlchemy ORM with the Flask app.
    db.init_app(app)

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
        featured_projects = (
            Project.query
            .filter_by(featured=True)
            .order_by(Project.date.desc(), Project.title.asc())
            .all()
        )

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
        normalized_slug = (slug or "").strip().lower()

        project = Project.query.filter_by(slug=normalized_slug).first()

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