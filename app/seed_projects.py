"""
seed_projects.py

Populate the database on deploy from admin_snapshot.json.

Run from repo root:
    python -m app.seed_projects
"""

from __future__ import annotations

import json
from pathlib import Path

from app.app import create_app
from app.models.models import Project, db


def _upsert_from_snapshot(existing: Project | None, data: dict) -> Project:
    p = existing or Project()
    p.slug = data["slug"]
    p.title = data["title"]
    p.primary_category = data["primary_category"]
    p.short_description = data["short_description"]
    p.full_description = data["full_description"]
    p.date = data.get("date")
    p.problem = data.get("problem")
    p.solution = data.get("solution")
    p.challenges = data.get("challenges")
    p.results = data.get("results")
    p.tags = data.get("tags", [])
    p.tech_stack = data.get("tech_stack", [])
    p.repo_url = data.get("repo_url")
    p.live_url = data.get("live_url")
    p.demo_url = data.get("demo_url")

    if existing is None:
        p.featured = data.get("featured", False)
        p.featured_order = data.get("featured_order")
        p.card_image = data.get("card_image")
        p.screenshots = data.get("screenshots", [])
        p.videos = data.get("videos", [])

    return p


def seed_projects() -> None:
    app = create_app()

    with app.app_context():
        snapshot_path = Path(app.root_path) / "data" / "admin_snapshot.json"
        snapshot_projects = json.loads(snapshot_path.read_text()).get("projects", [])
        snapshot_slugs = {p["slug"] for p in snapshot_projects}

        Project.query.filter(Project.slug.notin_(snapshot_slugs)).delete(
            synchronize_session=False
        )

        for data in snapshot_projects:
            existing = Project.query.filter_by(slug=data["slug"]).first()
            p = _upsert_from_snapshot(existing, data)
            if existing is None:
                db.session.add(p)

        db.session.commit()
        print(f"Database seeded successfully with {Project.query.count()} projects.")


if __name__ == "__main__":
    seed_projects()
