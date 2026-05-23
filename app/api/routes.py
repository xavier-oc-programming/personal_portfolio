"""
api/routes.py

Route handlers for the public REST API.

Endpoints
---------
GET /api/v1/projects                  All projects (supports ?category= and ?featured=true)
GET /api/v1/projects/<slug>           Single project by slug
GET /api/v1/categories                All categories with project counts
GET /api/v1/tags                      All tags with project counts

All responses use the envelope shape defined in api/utils.py.
All endpoints are read-only and require no authentication.
"""

from flask import jsonify, request

from app.api import api_bp
from app.api.utils import error_response, success_response
from app.models.models import Project

_ALLOWED_CATEGORIES = {"web", "data", "software", "ai-ml"}


@api_bp.get("/projects")
def get_projects():
    category = (request.args.get("category") or "").strip().lower()
    featured = (request.args.get("featured") or "").strip().lower()

    tag = (request.args.get("tag") or "").strip().lower()

    query = Project.query

    if category in _ALLOWED_CATEGORIES:
        query = query.filter_by(primary_category=category)

    if featured == "true":
        query = query.filter_by(featured=True)

    if tag:
        query = query.filter(Project.tags_json.ilike(f'%"{tag}"%'))

    projects = query.order_by(Project.date.desc(), Project.title.asc()).all()
    return jsonify(success_response([p.to_dict() for p in projects]))


@api_bp.get("/projects/<slug>")
def get_project(slug):
    normalized_slug = (slug or "").strip().lower()
    project = Project.query.filter_by(slug=normalized_slug).first()
    if not project:
        return jsonify(error_response("Project not found")), 404
    return jsonify(success_response(project.to_dict()))


@api_bp.get("/categories")
def get_categories():
    categories = [
        {
            "name": name,
            "slug": name,
            "project_count": Project.query.filter_by(primary_category=name).count(),
        }
        for name in sorted(_ALLOWED_CATEGORIES)
    ]
    return jsonify(success_response(categories))


@api_bp.get("/tags")
def get_tags():
    tag_counts: dict[str, int] = {}
    for project in Project.query.all():
        for tag in project.tags:
            normalized = str(tag).strip().lower()
            if normalized:
                tag_counts[normalized] = tag_counts.get(normalized, 0) + 1

    tags = [
        {"name": tag, "project_count": count}
        for tag, count in sorted(tag_counts.items())
    ]
    return jsonify(success_response(tags))


@api_bp.errorhandler(404)
def not_found(e):
    return jsonify(error_response("Resource not found")), 404


@api_bp.errorhandler(500)
def server_error(e):
    return jsonify(error_response("Internal server error")), 500
