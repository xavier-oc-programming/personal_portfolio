"""
seed_projects.py

Populate the portfolio database using the Phase 2 in-memory dataset.

Key responsibilities:
- Read project data from app/data/projects.py
- Upsert projects — insert new ones, update existing ones
- Preserve admin-uploaded media (card_image, screenshots, videos) on existing projects

Run from repo root:
    python -m app.seed_projects
"""

from __future__ import annotations

from app.app import create_app
from app.data.projects import PROJECTS
from app.models.models import Project, db


def seed_projects() -> None:
    """
    Upsert projects from PROJECTS into the database.

    Existing projects are updated for all content fields.
    Media fields (card_image, screenshots, videos) are only written
    if the seed data contains non-empty values — admin-uploaded media
    is preserved otherwise.

    New projects (slug not yet in DB) are inserted fresh.
    Projects in the DB whose slug is no longer in PROJECTS are deleted.
    """
    app = create_app()

    with app.app_context():
        seed_slugs = {p["slug"] for p in PROJECTS}

        # Remove projects no longer in the seed list
        Project.query.filter(Project.slug.notin_(seed_slugs)).delete(
            synchronize_session=False
        )

        for project_data in PROJECTS:
            links = project_data.get("links", {})
            media = project_data.get("media", {})

            existing = Project.query.filter_by(slug=project_data["slug"]).first()

            if existing:
                # Update content fields
                existing.title = project_data["title"]
                existing.primary_category = project_data["primary_category"]
                existing.short_description = project_data["short_description"]
                existing.full_description = project_data["full_description"]
                existing.featured = project_data.get("featured", False)
                existing.date = project_data.get("date")
                existing.problem = project_data.get("problem")
                existing.solution = project_data.get("solution")
                existing.challenges = project_data.get("challenges")
                existing.results = project_data.get("results")
                existing.repo_url = links.get("repo")
                existing.live_url = links.get("live")
                existing.demo_url = links.get("demo")
                existing.tags = project_data.get("tags", [])
                existing.tech_stack = project_data.get("tech_stack", [])

                # Only overwrite media if seed data has non-empty values
                if media.get("card_image"):
                    existing.card_image = media["card_image"]
                if media.get("screenshots"):
                    existing.screenshots = media["screenshots"]
                if media.get("videos"):
                    existing.videos = media["videos"]

            else:
                project = Project(
                    slug=project_data["slug"],
                    title=project_data["title"],
                    primary_category=project_data["primary_category"],
                    short_description=project_data["short_description"],
                    full_description=project_data["full_description"],
                    featured=project_data.get("featured", False),
                    date=project_data.get("date"),
                    problem=project_data.get("problem"),
                    solution=project_data.get("solution"),
                    challenges=project_data.get("challenges"),
                    results=project_data.get("results"),
                    repo_url=links.get("repo"),
                    live_url=links.get("live"),
                    demo_url=links.get("demo"),
                    card_image=media.get("card_image"),
                )
                project.tags = project_data.get("tags", [])
                project.tech_stack = project_data.get("tech_stack", [])
                project.screenshots = media.get("screenshots", [])
                project.videos = media.get("videos", [])
                db.session.add(project)

        db.session.commit()

        total = Project.query.count()
        print(f"Database seeded successfully with {total} projects.")


if __name__ == "__main__":
    seed_projects()
