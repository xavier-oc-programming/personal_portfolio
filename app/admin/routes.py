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
    POST /admin/projects/<slug>/media/screenshot - Upload screenshots (multi-file)
    POST /admin/projects/<slug>/media/screenshots/reorder - Reorder screenshots
    POST /admin/projects/<slug>/media/video    - Upload video
    POST /admin/projects/<slug>/media/delete   - Delete a media file
    GET  /admin/messages           - List contact messages
    POST /admin/messages/<id>/delete - Delete a message
    GET  /admin/tags               - List all tags with project counts
    POST /admin/tags/add           - Add a new tag to selected projects
    POST /admin/tags/assign        - Set exactly which projects carry a tag
    POST /admin/tags/rename        - Rename a tag across all projects
    POST /admin/tags/delete        - Delete a tag from all projects
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    abort,
    current_app,
    flash,
    jsonify,
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
    static_dir = Path(current_app.root_path) / "static"
    return static_dir / "images" / "projects" / slug


def _get_project_video_dir(slug: str) -> Path:
    static_dir = Path(current_app.root_path) / "static"
    return static_dir / "videos" / "projects" / slug


def _save_file(file, dest_dir: Path) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(file.filename)
    file.save(dest_dir / filename)
    return filename


def _backup_dir() -> Path:
    """Return the absolute path to the local backup directory."""
    return Path(current_app.root_path).parent / "data" / "backup"


def _backup_projects() -> None:
    """Write a timestamped snapshot of all projects to data/backup/."""
    backup_dir = _backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    backup_path = backup_dir / f"projects_{timestamp}.json"
    projects = Project.query.order_by(Project.id.asc()).all()
    data = [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "primary_category": p.primary_category,
            "short_description": p.short_description,
            "full_description": p.full_description,
            "featured": p.featured,
            "date": p.date,
            "problem": p.problem,
            "solution": p.solution,
            "challenges": p.challenges,
            "results": p.results,
            "tags": p.tags,
            "tech_stack": p.tech_stack,
            "screenshots": p.screenshots,
            "videos": p.videos,
            "card_image": p.card_image,
            "repo_url": p.repo_url,
            "live_url": p.live_url,
            "demo_url": p.demo_url,
        }
        for p in projects
    ]
    backup_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # Keep only the 3 most recent backups
    existing = sorted(backup_dir.glob("projects_*.json"))
    for old in existing[:-3]:
        old.unlink()


def _static_rel(path: Path) -> str:
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
        _backup_projects()

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
        _backup_projects()

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
    _backup_projects()
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

    files = request.files.getlist("screenshots")
    valid_files = [f for f in files if f and f.filename]

    if not valid_files:
        flash("No valid image files provided.", "danger")
        return redirect(url_for("admin.project_media", slug=slug))

    allowed_exts = {"jpg", "jpeg", "png", "gif", "webp"}
    dest = _get_project_static_dir(slug) / "screenshots"
    shots = project.screenshots
    count = 0

    for file in valid_files:
        ext = Path(secure_filename(file.filename)).suffix.lstrip(".").lower()
        if ext not in allowed_exts:
            continue
        filename = _save_file(file, dest)
        rel_path = _static_rel(dest / filename)
        if rel_path not in shots:
            shots.append(rel_path)
            count += 1

    if count:
        project.screenshots = shots
        db.session.commit()
        flash(f"{count} screenshot(s) uploaded.", "success")
    else:
        flash("No valid image files provided.", "danger")

    return redirect(url_for("admin.project_media", slug=slug))


@admin_bp.post("/projects/<slug>/media/screenshots/reorder")
@_require_admin
def media_reorder_screenshots(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    data = request.get_json(silent=True)
    if not data or "order" not in data:
        return jsonify({"error": "Missing order"}), 400
    new_order = data["order"]
    current = set(project.screenshots)
    if not all(p in current for p in new_order):
        return jsonify({"error": "Invalid paths"}), 400
    project.screenshots = new_order
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.post("/projects/<slug>/media/video")
@_require_admin
def media_upload_video(slug: str):
    project = Project.query.filter_by(slug=slug).first_or_404()
    form = VideoForm()

    if form.validate_on_submit() and form.video.data:
        dest = _get_project_video_dir(slug)
        filename = _save_file(form.video.data, dest)
        rel_path = str((dest / filename).relative_to(
            Path(current_app.root_path) / "static"
        )).replace("\\", "/")
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
    media_type = request.form.get("type")
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
        project.screenshots = [s for s in project.screenshots if s != rel_path]
        db.session.commit()
        if abs_path.exists():
            abs_path.unlink()
        flash("Screenshot removed.", "success")

    elif media_type == "video":
        project.videos = [v for v in project.videos if v != rel_path]
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


# ---------------------------------------------------------------------------
# Backups
# ---------------------------------------------------------------------------

@admin_bp.get("/backups")
@_require_admin
def backups():
    backup_dir = _backup_dir()
    files = []
    if backup_dir.exists():
        for f in sorted(backup_dir.glob("projects_*.json"), reverse=True):
            files.append({
                "filename": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    return render_template("admin/backups.html", backups=files)


@admin_bp.post("/backups/restore/<filename>")
@_require_admin
def backup_restore(filename: str):
    backup_dir = _backup_dir()
    backup_path = backup_dir / filename

    if not backup_path.exists() or not filename.startswith("projects_") or not filename.endswith(".json"):
        flash("Invalid backup file.", "danger")
        return redirect(url_for("admin.backups"))

    try:
        data = json.loads(backup_path.read_text())
    except (json.JSONDecodeError, OSError):
        flash("Could not read backup file.", "danger")
        return redirect(url_for("admin.backups"))

    _backup_projects()

    for entry in data:
        project = Project.query.filter_by(slug=entry["slug"]).first()
        if project is None:
            project = Project()
            db.session.add(project)
        project.slug = entry["slug"]
        project.title = entry["title"]
        project.primary_category = entry["primary_category"]
        project.short_description = entry["short_description"]
        project.full_description = entry["full_description"]
        project.featured = entry["featured"]
        project.date = entry.get("date")
        project.problem = entry.get("problem")
        project.solution = entry.get("solution")
        project.challenges = entry.get("challenges")
        project.results = entry.get("results")
        project.tags = entry.get("tags", [])
        project.tech_stack = entry.get("tech_stack", [])
        project.screenshots = entry.get("screenshots", [])
        project.videos = entry.get("videos", [])
        project.card_image = entry.get("card_image")
        project.repo_url = entry.get("repo_url")
        project.live_url = entry.get("live_url")
        project.demo_url = entry.get("demo_url")

    db.session.commit()
    flash(f"Restored {len(data)} projects from {filename}.", "success")
    return redirect(url_for("admin.backups"))


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

def _get_tag_counts() -> list[dict]:
    """Return all tags sorted alphabetically with a count of projects using each."""
    counts: dict[str, int] = {}
    for project in Project.query.all():
        for tag in project.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return [{"tag": t, "count": c} for t, c in sorted(counts.items())]


@admin_bp.get("/tags")
@_require_admin
def tags():
    all_projects = Project.query.order_by(Project.title.asc()).all()
    project_tags = {p.slug: p.tags for p in all_projects}
    return render_template(
        "admin/tags.html",
        tags=_get_tag_counts(),
        all_projects=all_projects,
        project_tags=project_tags,
    )


@admin_bp.post("/tags/add")
@_require_admin
def tag_add():
    tag = request.form.get("tag", "").strip()
    slugs = request.form.getlist("slugs")

    if not tag:
        flash("Tag name is required.", "danger")
        return redirect(url_for("admin.tags"))

    if not slugs:
        flash("Select at least one project.", "danger")
        return redirect(url_for("admin.tags"))

    updated = 0
    for project in Project.query.filter(Project.slug.in_(slugs)).all():
        if tag not in project.tags:
            project.tags = project.tags + [tag]
            updated += 1

    db.session.commit()
    _backup_projects()
    flash(f"Added tag '{tag}' to {updated} project(s).", "success")
    return redirect(url_for("admin.tags"))


@admin_bp.post("/tags/assign")
@_require_admin
def tag_assign():
    tag = request.form.get("tag", "").strip()
    selected_slugs = set(request.form.getlist("slugs"))

    if not tag:
        flash("No tag specified.", "danger")
        return redirect(url_for("admin.tags"))

    added = removed = 0
    for project in Project.query.all():
        has_tag = tag in project.tags
        should_have = project.slug in selected_slugs
        if should_have and not has_tag:
            project.tags = project.tags + [tag]
            added += 1
        elif not should_have and has_tag:
            project.tags = [t for t in project.tags if t != tag]
            removed += 1

    db.session.commit()
    _backup_projects()
    flash(f"Tag '{tag}': {added} added, {removed} removed.", "success")
    return redirect(url_for("admin.tags"))


@admin_bp.post("/tags/rename")
@_require_admin
def tag_rename():
    old_tag = request.form.get("old_tag", "").strip()
    new_tag = request.form.get("new_tag", "").strip()

    if not old_tag or not new_tag:
        flash("Both old and new tag names are required.", "danger")
        return redirect(url_for("admin.tags"))

    if old_tag == new_tag:
        flash("New tag name is the same as the old one.", "warning")
        return redirect(url_for("admin.tags"))

    updated = 0
    for project in Project.query.all():
        if old_tag in project.tags:
            project.tags = [new_tag if t == old_tag else t for t in project.tags]
            updated += 1

    db.session.commit()
    _backup_projects()
    flash(f"Renamed '{old_tag}' → '{new_tag}' across {updated} project(s).", "success")
    return redirect(url_for("admin.tags"))


@admin_bp.post("/tags/delete")
@_require_admin
def tag_delete():
    tag = request.form.get("tag", "").strip()

    if not tag:
        flash("No tag specified.", "danger")
        return redirect(url_for("admin.tags"))

    updated = 0
    for project in Project.query.all():
        if tag in project.tags:
            project.tags = [t for t in project.tags if t != tag]
            updated += 1

    db.session.commit()
    _backup_projects()
    flash(f"Deleted tag '{tag}' from {updated} project(s).", "success")
    return redirect(url_for("admin.tags"))
