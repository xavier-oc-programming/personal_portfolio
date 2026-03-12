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

import time
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from config import get_config_class
from forms import ContactForm, MAX_EMAIL_LENGTH, MAX_MESSAGE_LENGTH, MAX_NAME_LENGTH
from models.models import ContactMessage, Project, db


load_dotenv()


ALLOWED_CATEGORIES = {"web", "data", "software"}
ALLOWED_SORTS = {"az", "newest", "oldest"}

MIN_FORM_FILL_SECONDS = 3
CONTACT_RATE_LIMIT_SECONDS = 3


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
    Normalize, trim, and safely sanitize short user text input.
    """
    normalized_value = " ".join((value or "").strip().split())
    sanitized_value = escape(normalized_value)

    if max_length is not None:
        return sanitized_value[:max_length]

    return sanitized_value


def _sanitize_message_input(value: str, *, max_length: int | None = None) -> str:
    """
    Normalize and sanitize multi-line message content while preserving
    intentional line breaks.
    """
    raw_value = (value or "").strip()

    cleaned_lines = [line.strip() for line in raw_value.splitlines()]
    normalized_value = "\n".join(line for line in cleaned_lines if line)

    sanitized_value = escape(normalized_value)

    if max_length is not None:
        return sanitized_value[:max_length]

    return sanitized_value


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
        form = ContactForm()

        if request.method == "GET":
            session["contact_form_loaded_at"] = time.time()
            return render_template("contact.html", form=form)

        if form.company.data:
            flash("Invalid submission detected.", "danger")
            session["contact_form_loaded_at"] = time.time()
            return render_template("contact.html", form=form), 400

        form_loaded_at = session.get("contact_form_loaded_at")

        if form_loaded_at is None or (time.time() - form_loaded_at) < MIN_FORM_FILL_SECONDS:
            flash("Please wait a moment before submitting the form.", "danger")
            session["contact_form_loaded_at"] = time.time()
            return render_template("contact.html", form=form), 400

        last_submission_at = session.get("last_contact_submission_at")

        if (
            last_submission_at is not None
            and (time.time() - last_submission_at) < CONTACT_RATE_LIMIT_SECONDS
        ):
            flash("Please wait a minute before sending another message.", "danger")
            return render_template("contact.html", form=form), 429

        if form.validate_on_submit():
            sanitized_name = _sanitize_text_input(
                form.name.data,
                max_length=MAX_NAME_LENGTH,
            )
            sanitized_email = _sanitize_text_input(
                form.email.data,
                max_length=MAX_EMAIL_LENGTH,
            )
            sanitized_message = _sanitize_message_input(
                form.message.data,
                max_length=MAX_MESSAGE_LENGTH,
            )

            contact_message = ContactMessage(
                name=sanitized_name,
                email=sanitized_email,
                message=sanitized_message,
            )

            db.session.add(contact_message)
            db.session.commit()

            session["last_contact_submission_at"] = time.time()

            flash("Your message was sent successfully.", "success")
            return redirect(url_for("contact"))

        if form.errors:
            for field_errors in form.errors.values():
                for error_message in field_errors:
                    flash(error_message, "danger")

            return render_template("contact.html", form=form), 400

        return render_template("contact.html", form=form)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=app.debug)