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
- Persist contact form submissions to the database.
- Prepare the SQLite database directory/file strategy.
- Initialize SQLAlchemy as the ORM layer.
- Create database tables that match the unified project schema.

Run locally (from repo root):
    python app/app.py
"""

from __future__ import annotations

import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

from config import get_config_class
from models.models import ContactMessage, Project, db


load_dotenv()


ALLOWED_CATEGORIES = {"web", "data", "software"}
ALLOWED_SORTS = {"az", "newest", "oldest"}

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

MAX_NAME_LENGTH = 60
MAX_EMAIL_LENGTH = 254
MAX_MESSAGE_LENGTH = 2000


def _normalize_category(category: str | None) -> str | None:
    if not category:
        return None

    normalized_category = category.strip().lower()

    if normalized_category not in ALLOWED_CATEGORIES:
        return None

    return normalized_category


def _normalize_tag(tag: str | None) -> str | None:
    if not tag:
        return None

    normalized_tag = tag.strip().lower()

    if not normalized_tag:
        return None

    return normalized_tag


def _normalize_sort(sort_key: str | None) -> str:
    normalized_sort = (sort_key or "az").strip().lower()

    if normalized_sort not in ALLOWED_SORTS:
        return "az"

    return normalized_sort


def _apply_database_filters(
    category: str | None = None,
    tag: str | None = None,
):
    normalized_category = _normalize_category(category)
    normalized_tag = _normalize_tag(tag)

    query = Project.query

    if normalized_category:
        query = query.filter(Project.primary_category == normalized_category)

    if normalized_tag:
        query = query.filter(Project.tags_json.ilike(f'%"{normalized_tag}"%'))

    return query


def _apply_sort(query, sort_key: str | None):
    normalized_sort = _normalize_sort(sort_key)

    if normalized_sort == "az":
        return query.order_by(Project.title.asc()), normalized_sort

    if normalized_sort == "newest":
        return query.order_by(Project.date.desc(), Project.title.asc()), normalized_sort

    return query.order_by(Project.date.asc(), Project.title.asc()), normalized_sort


def _get_available_tags() -> list[str]:
    tag_set: set[str] = set()

    all_projects = Project.query.all()

    for project in all_projects:
        for tag in project.tags:
            normalized_tag = str(tag).strip().lower()

            if normalized_tag:
                tag_set.add(normalized_tag)

    return sorted(tag_set)


def _get_category_counts() -> dict[str, int]:
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
    database_path = app.config.get("DATABASE_PATH")

    if not database_path:
        return

    if isinstance(database_path, str):
        database_path = Path(database_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.touch(exist_ok=True)


def _sanitize_text_input(value: str, *, max_length: int | None = None) -> str:
    """
    Normalize, trim, and safely sanitize user text input.

    What this function does:
    - Replaces repeated whitespace/newlines with single spaces between words.
    - Strips leading and trailing whitespace.
    - Escapes HTML-sensitive characters.
    - Optionally truncates to a maximum allowed length.
    """
    normalized_value = " ".join((value or "").strip().split())
    sanitized_value = escape(normalized_value)

    if max_length is not None:
        return sanitized_value[:max_length]

    return sanitized_value


def _sanitize_message_input(value: str, *, max_length: int | None = None) -> str:
    """
    Normalize and sanitize multi-line message content.

    Unlike short one-line fields such as name/email, messages should preserve
    paragraph breaks. This function:
    - Strips leading/trailing whitespace.
    - Normalizes line-by-line spacing.
    - Preserves intentional newlines.
    - Escapes HTML-sensitive characters.
    - Optionally truncates to a maximum length.
    """
    raw_value = (value or "").strip()

    cleaned_lines = [line.strip() for line in raw_value.splitlines()]
    normalized_value = "\n".join(line for line in cleaned_lines if line)

    sanitized_value = escape(normalized_value)

    if max_length is not None:
        return sanitized_value[:max_length]

    return sanitized_value


def _is_valid_email(email: str) -> bool:
    """
    Validate email format with a simple production-appropriate regex.
    """
    if not email:
        return False

    return EMAIL_REGEX.fullmatch(email) is not None


def _get_contact_form_data() -> dict[str, str]:
    """
    Read raw contact form values from the request and return a clean dict
    suitable for re-rendering the form after validation errors.
    """
    return {
        "name": (request.form.get("name") or "").strip(),
        "email": (request.form.get("email") or "").strip(),
        "message": (request.form.get("message") or "").strip(),
    }


def _validate_contact_form(form_data: dict[str, str]) -> list[str]:
    """
    Validate the contact form and return a list of human-readable error messages.
    """
    errors: list[str] = []

    name = form_data["name"]
    email = form_data["email"]
    message = form_data["message"]

    if not name:
        errors.append("Name is required.")
    elif len(name) < 2:
        errors.append("Name must be at least 2 characters.")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"Name must be {MAX_NAME_LENGTH} characters or fewer.")

    if not email:
        errors.append("Email is required.")
    elif not _is_valid_email(email):
        errors.append("Please enter a valid email address.")
    elif len(email) > MAX_EMAIL_LENGTH:
        errors.append(f"Email must be {MAX_EMAIL_LENGTH} characters or fewer.")

    if not message:
        errors.append("Message is required.")
    elif len(message) < 10:
        errors.append("Message must be at least 10 characters.")
    elif len(message) > MAX_MESSAGE_LENGTH:
        errors.append(f"Message must be {MAX_MESSAGE_LENGTH} characters or fewer.")

    return errors


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config_class())

    _ensure_database_directory_and_file(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_global_template_vars():
        return {
            "current_year": datetime.now().year,
        }

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

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        form_data = {
            "name": "",
            "email": "",
            "message": "",
        }

        if request.method == "POST":
            form_data = _get_contact_form_data()
            validation_errors = _validate_contact_form(form_data)

            if validation_errors:
                for error_message in validation_errors:
                    flash(error_message, "danger")

                return render_template(
                    "contact.html",
                    form_data=form_data,
                    MAX_NAME_LENGTH=MAX_NAME_LENGTH,
                    MAX_EMAIL_LENGTH=MAX_EMAIL_LENGTH,
                    MAX_MESSAGE_LENGTH=MAX_MESSAGE_LENGTH,
                ), 400

            sanitized_name = _sanitize_text_input(
                form_data["name"],
                max_length=MAX_NAME_LENGTH,
            )
            sanitized_email = _sanitize_text_input(
                form_data["email"],
                max_length=MAX_EMAIL_LENGTH,
            )
            sanitized_message = _sanitize_message_input(
                form_data["message"],
                max_length=MAX_MESSAGE_LENGTH,
            )

            contact_message = ContactMessage(
                name=sanitized_name,
                email=sanitized_email,
                message=sanitized_message,
            )

            db.session.add(contact_message)
            db.session.commit()

            flash("Your message was sent successfully.", "success")
            return redirect(url_for("contact"))

        return render_template(
            "contact.html",
            form_data=form_data,
            MAX_NAME_LENGTH=MAX_NAME_LENGTH,
            MAX_EMAIL_LENGTH=MAX_EMAIL_LENGTH,
            MAX_MESSAGE_LENGTH=MAX_MESSAGE_LENGTH,
        )

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=app.debug)