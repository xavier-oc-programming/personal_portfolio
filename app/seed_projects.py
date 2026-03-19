"""
seed_projects.py

Populate the portfolio database using the Phase 2 in-memory dataset.

Key responsibilities:
- Read project data from app/data/projects.py
- Clear existing rows from the projects table
- Insert the current project dataset into SQLite

Run from repo root:
    python app/seed_projects.py
"""

from __future__ import annotations

from app.app import create_app
from app.data.projects import PROJECTS
from app.models.models import Project, db


def seed_projects() -> None:
    """
    Populate the projects table from PROJECTS if it is currently empty.
    Skips seeding if rows already exist to preserve any live edits.
    """
    app = create_app()

    with app.app_context():
        if Project.query.count() > 0:
            print("Database already seeded — skipping.")
            return

        for project_data in PROJECTS:
            links = project_data.get("links", {})
            media = project_data.get("media", {})

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

        print(f"Database seeded successfully with {len(PROJECTS)} projects.")


if __name__ == "__main__":
    seed_projects()