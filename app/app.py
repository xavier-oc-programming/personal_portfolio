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
- Send email notifications for new contact submissions via Resend.
- Apply spam-mitigation protections to the contact form.
- Prepare the SQLite database directory/file strategy.
- Initialize SQLAlchemy as the ORM layer.
- Create database tables that match the unified project schema.
- Expose global SEO and analytics metadata for templates.

Run locally (from repo root):
    python -m app.app
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import resend

from flask import Flask, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect

from app.admin import admin_bp
from app.api import api_bp
from app.assistant import assistant_bp, limiter as assistant_limiter
from app.assistant.rag import RAGEngine
from app.config import get_config_class
from app.forms import ContactForm, MAX_EMAIL_LENGTH, MAX_MESSAGE_LENGTH, MAX_NAME_LENGTH
from app.models.models import ContactMessage, Project, db

ALLOWED_CATEGORIES = {"web", "data", "software"}
ALLOWED_SORTS = {"az", "newest", "oldest"}

MIN_FORM_FILL_SECONDS = 8
CONTACT_RATE_LIMIT_SECONDS = 60


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

    normalized_tag = tag.strip()

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
            t = str(tag).strip()
            if t:
                tag_set.add(t)

    return sorted(tag_set, key=str.lower)


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


def _normalize_text_input(value: str, *, max_length: int | None = None) -> str:
    normalized_value = " ".join((value or "").strip().split())

    if max_length is not None:
        return normalized_value[:max_length]

    return normalized_value


def _normalize_message_input(value: str, *, max_length: int | None = None) -> str:
    raw_value = (value or "").strip()

    cleaned_lines = [line.strip() for line in raw_value.splitlines()]
    normalized_value = "\n".join(line for line in cleaned_lines if line)

    if max_length is not None:
        return normalized_value[:max_length]

    return normalized_value


def _start_contact_form_timer() -> None:
    session["contact_form_loaded_at"] = time.time()


def _is_honeypot_triggered(form: ContactForm) -> bool:
    return bool((form.company.data or "").strip())


def _is_form_submitted_too_quickly() -> bool:
    form_loaded_at = session.get("contact_form_loaded_at")

    if form_loaded_at is None:
        return True

    return (time.time() - form_loaded_at) < MIN_FORM_FILL_SECONDS


def _is_rate_limited() -> bool:
    last_submission_at = session.get("last_contact_submission_at")

    if last_submission_at is None:
        return False

    return (time.time() - last_submission_at) < CONTACT_RATE_LIMIT_SECONDS


def _mark_contact_submission_time() -> None:
    session["last_contact_submission_at"] = time.time()


def _send_contact_notification(
    *,
    app: Flask,
    sender_name: str,
    sender_email: str,
    message_body: str,
    submitted_at: datetime,
) -> bool:
    recipient = app.config.get("CONTACT_NOTIFICATION_EMAIL")

    if not recipient:
        app.logger.warning(
            "CONTACT_NOTIFICATION_EMAIL is not configured. "
            "Skipping contact notification email."
        )
        return False

    resend.api_key = app.config.get("RESEND_API_KEY")

    body = (
        "A new message was submitted through your portfolio contact form.\n\n"
        f"Name: {sender_name}\n"
        f"Email: {sender_email}\n"
        f"Submitted at: {submitted_at.isoformat()}\n\n"
        "Message:\n"
        "--------\n"
        f"{message_body}\n"
    )

    try:
        resend.Emails.send({
            "from": "portfolio@xavieroc.dev",
            "to": recipient,
            "subject": "New portfolio contact message",
            "text": body,
        })
        return True
    except Exception:
        app.logger.exception("Failed to send contact notification email.")
        return False


def _sync_from_snapshot(app: Flask) -> None:
    """
    Upsert all projects from admin_snapshot.json into the local database.

    Runs only in development so the local DB stays in sync with the
    latest snapshot committed to the repository without any manual steps.
    """
    snapshot_path = Path(__file__).parent / "data" / "admin_snapshot.json"

    if not snapshot_path.exists():
        app.logger.warning("admin_snapshot.json not found — skipping sync.")
        return

    with open(snapshot_path) as f:
        snapshot = json.load(f)

    projects_data = snapshot.get("projects", [])

    for record in projects_data:
        project = Project.query.filter_by(slug=record["slug"]).first()

        if project is None:
            project = Project(slug=record["slug"])
            db.session.add(project)

        project.title             = record["title"]
        project.primary_category  = record["primary_category"]
        project.short_description = record["short_description"]
        project.full_description  = record["full_description"]
        project.featured          = record.get("featured", False)
        project.featured_order    = record.get("featured_order")
        project.date              = record.get("date")
        project.problem           = record.get("problem")
        project.solution          = record.get("solution")
        project.challenges        = record.get("challenges")
        project.results           = record.get("results")
        project.tags              = record.get("tags", [])
        project.tech_stack        = record.get("tech_stack", [])
        project.screenshots       = record.get("screenshots", [])
        project.videos            = record.get("videos", [])
        project.card_image        = record.get("card_image")
        project.repo_url          = record.get("repo_url")
        project.live_url          = record.get("live_url")
        project.demo_url          = record.get("demo_url")

    db.session.commit()

    # Delete projects that exist in the DB but are no longer in the snapshot.
    snapshot_slugs = {record["slug"] for record in projects_data}
    removed = 0
    for project in Project.query.all():
        if project.slug not in snapshot_slugs:
            db.session.delete(project)
            removed += 1
    if removed:
        db.session.commit()
        app.logger.info("Removed %d projects not in admin_snapshot.json.", removed)

    app.logger.info("Synced %d projects from admin_snapshot.json.", len(projects_data))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config_class())

    _ensure_database_directory_and_file(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        if app.config.get("DEBUG"):
            _sync_from_snapshot(app)

    csrf = CSRFProtect(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.config["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY")

    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(assistant_bp)
    csrf.exempt(assistant_bp)

    assistant_limiter.init_app(app)

    rag_engine = RAGEngine()
    rag_engine.init_app(app)

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        desc = str(error.description).lower() if hasattr(error, "description") else ""
        if "per day" in desc:
            msg = "Sorry — the assistant has hit its daily request limit. Please try again tomorrow."
        else:
            msg = "Sorry — too many requests. Please wait a minute and try again."
        return jsonify({"error": msg}), 429

    @app.context_processor
    def inject_global_template_vars():
        site_url = app.config["SITE_URL"]

        current_url = request.url
        canonical_url = current_url.split("?")[0]

        default_og_image = f"{site_url}{url_for('static', filename='images/og/default-og-image.png')}"

        return {
            "current_year": datetime.now().year,
            "site_url": site_url,
            "site_name": app.config["SITE_NAME"],
            "default_meta_description": app.config["DEFAULT_META_DESCRIPTION"],
            "google_analytics_id": app.config.get("GOOGLE_ANALYTICS_ID"),
            "canonical_url": canonical_url,
            "default_og_type": "website",
            "default_og_image": default_og_image,
            "request_path": request.path,
        }

    @app.get("/robots.txt")
    def robots_txt():
        site_url = app.config["SITE_URL"]
        content = f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n"
        return Response(content, mimetype="text/plain")

    @app.get("/sitemap.xml")
    def sitemap_xml():
        site_url = app.config["SITE_URL"]
        pages = [
            (site_url + "/", "weekly", "1.0"),
            (site_url + "/about", "monthly", "0.9"),
            (site_url + "/projects", "weekly", "0.9"),
            (site_url + "/contact", "monthly", "0.7"),
        ]
        urls = "".join(
            f"<url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>"
            for loc, freq, pri in pages
        )
        xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0/9/">{urls}</urlset>'
        return Response(xml, mimetype="application/xml")

    @app.get("/favicon.ico")
    def favicon_ico():
        return redirect(url_for("static", filename="images/favicon.png"), code=301)

    @app.get("/")
    def home():
        featured_projects = (
            Project.query
            .filter_by(featured=True)
            .order_by(db.func.coalesce(Project.featured_order, 999999).asc(), Project.title.asc())
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
            _start_contact_form_timer()
            return render_template("contact.html", form=form)

        if _is_honeypot_triggered(form):
            app.logger.warning(
                "Contact form honeypot triggered from IP %s.",
                request.remote_addr,
            )
            flash("Invalid submission detected.", "danger")
            _start_contact_form_timer()
            return render_template("contact.html", form=form), 400

        if _is_form_submitted_too_quickly():
            app.logger.warning(
                "Contact form submitted too quickly from IP %s.",
                request.remote_addr,
            )
            flash("Please take a moment before submitting the form.", "danger")
            _start_contact_form_timer()
            return render_template("contact.html", form=form), 400

        if _is_rate_limited():
            app.logger.warning(
                "Contact form rate limit triggered from IP %s.",
                request.remote_addr,
            )
            flash("Please wait about a minute before sending another message.", "danger")
            _start_contact_form_timer()
            return render_template("contact.html", form=form), 429

        if form.validate_on_submit():
            normalized_name = _normalize_text_input(
                form.name.data,
                max_length=MAX_NAME_LENGTH,
            )
            normalized_email = _normalize_text_input(
                form.email.data,
                max_length=MAX_EMAIL_LENGTH,
            )
            normalized_message = _normalize_message_input(
                form.message.data,
                max_length=MAX_MESSAGE_LENGTH,
            )

            contact_message = ContactMessage(
                name=normalized_name,
                email=normalized_email,
                message=normalized_message,
            )

            try:
                db.session.add(contact_message)
                db.session.commit()
            except Exception:
                db.session.rollback()
                app.logger.exception("Failed to store contact message.")

                flash(
                    "Something went wrong while saving your message. Please try again.",
                    "danger",
                )
                _start_contact_form_timer()
                return render_template("contact.html", form=form), 500

            _mark_contact_submission_time()

            email_sent = _send_contact_notification(
                app=app,
                sender_name=contact_message.name,
                sender_email=contact_message.email,
                message_body=contact_message.message,
                submitted_at=contact_message.created_at,
            )

            if email_sent:
                flash("Your message was sent successfully.", "success")
            else:
                flash(
                    "Your message was saved successfully, but the email notification could not be sent.",
                    "warning",
                )

            return redirect(url_for("contact"))

        if form.errors:
            for field_errors in form.errors.values():
                for error_message in field_errors:
                    flash(error_message, "danger")

            _start_contact_form_timer()
            return render_template("contact.html", form=form), 400

        _start_contact_form_timer()
        return render_template("contact.html", form=form)

    @app.get("/api")
    def api_docs():
        return render_template("api_docs.html")

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config["DEBUG"],
    )