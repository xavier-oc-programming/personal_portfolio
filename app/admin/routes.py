"""
app/admin/routes.py

All routes for the admin blueprint.

Routes:
    GET  /admin/login              - Login form
    POST /admin/login              - Authenticate
    GET  /admin/logout             - Log out
    GET  /admin/                   - Dashboard
    GET  /admin/projects           - List all projects
    GET  /admin/projects/new       - New project form
    POST /admin/projects/new       - Create project
    GET  /admin/projects/<slug>    - Edit project form
    POST /admin/projects/<slug>    - Update project
    POST /admin/projects/<slug>/delete         - Delete project
    GET  /admin/projects/<slug>/media          - Media manager
    POST /admin/projects/<slug>/media/card     - Upload card image
    POST /admin/projects/<slug>/media/screenshot - Upload screenshot
    POST /admin/projects/<slug>/media/video    - Upload video
    POST /admin/projects/<slug>/media/delete   - Delete a media file
    GET  /admin/messages           - List contact messages
    POST /admin/messages/<id>/delete - Delete a message
"""

from __future__ import annotations

import os
from functools import wraps
from pathlib import Path

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app.admin import admin_bp
from app.admin.forms import CardImageForm, ProjectForm, ScreenshotForm, VideoForm
from app.models.models import ContactMessage, Project, db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


def _split_csv(value: str) -> list[str]:
    """Convert a comma-separated string into a cleaned list of non-empty strings."""
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _get_project_static_dir(slug: str) -> Path:
    """Return the absolute path to app/static/images/projects/<slug>/."""
    static_dir = Path(current_app.root_path) / "static"
    return static_dir / "images" / "projects" / slug


def _get_project_video_dir(slug: str) -> Path:
    """Return the absolute path to app/static/videos/projects/<slug>/."""
    static_dir = Path(current_app.root_path) / "static"
    return static_dir / "videos" / "projects" / slug


def _save_file(file, dest_dir: Path) -> str:
    """Save an uploaded file to dest_dir and return the filename."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(file.filename)
    file.save(dest_dir / filename)
    return filename


def _static_rel(path: Path) -> str:
    """Convert an absolute path inside static/ to a relative path for url_for('static', ...)."""
    static_dir = Path(current_app.root_path) / "static"
    return str(path.relative_to(static_dir)).replace("\\", "/")


def _populate_project_from_form(project: Project, form: ProjectForm) -> None:
    project.title = form.title.data.strip()
    project.slug = form.slug.data.strip().lower()
    project.primary_category = form.primary_category.data
    project.short_description = form.short_description.data.strip()
    project.full_description = form.full_description.data.strip()
    project.featured = form.featured.data
    project.date = (form.date.data or "").strip() or None
    project.problem = (form.problem.data or "").strip() or None
    project.solution = (form.solution.data or "").strip() or None
    project.challenges = (form.challenges.data or "").strip() or None
    project.results = (form.results.data or "").strip() or None
    project.tags = _split_csv(form.tags.data)
    project.tech_stack = _split_csv(form.tech_stack.data)
    project.repo_url = (form.repo_url.data or "").strip() or None
    project.live_url = (form.live_url.data or "").strip() or None
    project.demo_url = (form.demo_url.data or "").strip() or None


def _populate_form_from_project(form: ProjectForm, project: Project) -> None:
    form.title.data = project.title
    form.slug.data = project.slug
    form.primary_category.data = project.primary_category
    form.short_description.data = project.short_description
    form.full_description.data = project.full_description
    form.featured.data = project.featured
    form.date.data = project.date or ""
    form.problem.data = project.problem or ""
    form.solution.data = project.solution or ""
    form.challenges.data = project.challenges or ""
    form.results.data = project.results or ""
    form.tags.data = ", ".join(project.tags)
    form.tech_stack.data = ", ".join(project.tech_stack)
    form.repo_url.data = project.repo_url or ""
    form.live_url.data = project.live_url or ""
    form.demo_url.data = project.demo_url or ""


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    error = None

    if request.method == "POST":
        password = request.form.get("password", "")
        admin_password = current_app.config.get("ADMIN_PASSWORD", "admin")

        if password == admin_password:
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))

        error = "Incorrect password."

    return render_template("admin/login.html", error=error)


@admin_bp.get("/logout")
def logout():
    session.pop("admin_logged_in", None)
    flash("Logged out.", "info")
    return redirect(url_for("admin.login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin_bp.get("/")
@_require_admin
def dashboard():
    total_projects = Project.query.count()
    featured_count = Project.query.filter_by(featured=True).count()
    total_messages = ContactMessage.query.count()
    recent_messages = (
        ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    )
    category_counts = {
        "web": Project.query.filter_by(primary_category="web").count(),
        "data": Project.query.filter_by(primary_category="data").count(),
        "software": Project.query.filter_by(primary_category="software").count(),
    }
    projects_with_card = Project.query.filter(Project.card_image.isnot(None)).count()

    return render_template(
        "admin/dashboard.html",
        total_projects=total_projects,
        featured_count=featured_count,
        total_messages=total_messages,
        recent_messages=recent_messages,
        category_counts=category_counts,
        projects_with_card=projects_with_card,
    )


# ---------------------------------------------------------------------------
# Projects — list
# ---------------------------------------------------------------------------

@admin_bp.get("/projects")
@_require_admin
def projects():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Project.query

    if search:
        query = query.filter(Project.title.ilike(f"%{search}%"))

    if category in ("web", "data", "software"):
        query = query.filter_by(primary_category=category)

    all_projects = query.order_by(Project.title.asc()).all()

    return render_template(
        "admin/projects.html",
        projects=all_projects,
        search=search,
        active_category=category,
    )


# ---------------------------------------------------------------------------
# Projects — create
# ---------------------------------------------------------------------------

@admin_bp.route("/projects/new", methods=["GET", "POST"])
@_require_admin
def project_new():
    form = ProjectForm()

    if form.validate_on_submit():
        if Project.query.filter_by(slug=form.slug.data.strip().lower()).first():
            flash(f"Slug '{form.slug.data}' is already taken.", "danger")
            return render_template("admin/project_form.html", form=form, project=None)

        project = Project()
        _populate_project_from_form(project, form)

        db.session.add(project)
        db.session.commit()

        flash(f"Project '{project.title}' created.", "success")
        return redirect(url_for("admin.project_edit", slug=project.slug))

    if form.errors:
        for errors in form.errors.values():
            for err in errors:
                flash(err, "danger")

    return render_template("admin/project_form.html", form=form, project=None)


# ---------------------------------------------------------------------------
# Projects — edit
# ---------------------------------------------------------------------------

@admin_bp.route("/projects/<slug>", methods=["GET", "POST"])
@_require_admin
def project_edit(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    form = ProjectForm()

    if request.method == "GET":
        _populate_form_from_project(form, project)
        return render_template("admin/project_form.html", form=form, project=project)

    if form.validate_on_submit():
        new_slug = form.slug.data.strip().lower()
        if new_slug != project.slug:
            if Project.query.filter_by(slug=new_slug).first():
                flash(f"Slug '{new_slug}' is already taken.", "danger")
                return render_template("admin/project_form.html", form=form, project=project)

        _populate_project_from_form(project, form)
        db.session.commit()

        flash(f"Project '{project.title}' updated.", "success")
        return redirect(url_for("admin.project_edit", slug=project.slug))

    if form.errors:
        for errors in form.errors.values():
            for err in errors:
                flash(err, "danger")

    return render_template("admin/project_form.html", form=form, project=project)


# ---------------------------------------------------------------------------
# Projects — delete
# ---------------------------------------------------------------------------

@admin_bp.post("/projects/<slug>/delete")
@_require_admin
def project_delete(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    title = project.title
    db.session.delete(project)
    db.session.commit()
    flash(f"Project '{title}' deleted.", "success")
    return redirect(url_for("admin.projects"))


# ---------------------------------------------------------------------------
# Media manager
# ---------------------------------------------------------------------------

@admin_bp.get("/projects/<slug>/media")
@_require_admin
def project_media(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()

    return render_template(
        "admin/media.html",
        project=project,
        card_form=CardImageForm(),
        screenshot_form=ScreenshotForm(),
        video_form=VideoForm(),
    )


@admin_bp.post("/projects/<slug>/media/card")
@_require_admin
def media_upload_card(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    form = CardImageForm()

    if form.validate_on_submit() and form.card_image.data:
        dest = _get_project_static_dir(slug) / "card"
        filename = _save_file(form.card_image.data, dest)
        project.card_image = _static_rel(dest / filename)
        db.session.commit()
        flash("Card image uploaded.", "success")
    else:
        flash("No valid image file provided.", "danger")

    return redirect(url_for("admin.project_media", slug=slug))


@admin_bp.post("/projects/<slug>/media/screenshot")
@_require_admin
def media_upload_screenshot(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    form = ScreenshotForm()

    if form.validate_on_submit() and form.screenshot.data:
        dest = _get_project_static_dir(slug) / "screenshots"
        filename = _save_file(form.screenshot.data, dest)
        rel_path = _static_rel(dest / filename)
        shots = project.screenshots
        if rel_path not in shots:
            shots.append(rel_path)
            project.screenshots = shots
            db.session.commit()
        flash("Screenshot uploaded.", "success")
    else:
        flash("No valid image file provided.", "danger")

    return redirect(url_for("admin.project_media", slug=slug))


@admin_bp.post("/projects/<slug>/media/video")
@_require_admin
def media_upload_video(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    form = VideoForm()

    if form.validate_on_submit() and form.video.data:
        dest = _get_project_video_dir(slug)
        filename = _save_file(form.video.data, dest)

        static_dir = Path(current_app.root_path) / "static"
        # videos live outside images/ — compute relative to static parent
        videos_static_dir = Path(current_app.root_path) / "static"
        rel_path = str((dest / filename).relative_to(videos_static_dir)).replace("\\", "/")

        vids = project.videos
        if rel_path not in vids:
            vids.append(rel_path)
            project.videos = vids
            db.session.commit()
        flash("Video uploaded.", "success")
    else:
        flash("No valid video file provided.", "danger")

    return redirect(url_for("admin.project_media", slug=slug))


@admin_bp.post("/projects/<slug>/media/delete")
@_require_admin
def media_delete(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    media_type = request.form.get("type")  # "card", "screenshot", "video"
    rel_path = request.form.get("path", "")

    static_dir = Path(current_app.root_path) / "static"
    abs_path = static_dir / rel_path

    if media_type == "card":
        project.card_image = None
        db.session.commit()
        if abs_path.exists():
            abs_path.unlink()
        flash("Card image removed.", "success")

    elif media_type == "screenshot":
        shots = [s for s in project.screenshots if s != rel_path]
        project.screenshots = shots
        db.session.commit()
        if abs_path.exists():
            abs_path.unlink()
        flash("Screenshot removed.", "success")

    elif media_type == "video":
        vids = [v for v in project.videos if v != rel_path]
        project.videos = vids
        db.session.commit()
        if abs_path.exists():
            abs_path.unlink()
        flash("Video removed.", "success")

    else:
        flash("Unknown media type.", "danger")

    return redirect(url_for("admin.project_media", slug=slug))


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@admin_bp.get("/messages")
@_require_admin
def messages():
    all_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/messages.html", messages=all_messages)


@admin_bp.post("/messages/<int:message_id>/delete")
@_require_admin
def message_delete(message_id: int):
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("admin.messages"))
