"""
app/data/projects.py

In-memory project dataset for Phase 2.

Projects live here (NOT hardcoded in templates).
Each project follows the Phase 1 schema.

Schema:
- slug (unique)
- title
- primary_category (web/data/software)
- tags (list[str])
- short_description
- full_description
- tech_stack (list[str])
- links (dict: repo/live/demo)
- image (optional: path string)
- featured (optional: bool)
- date (optional but recommended for newest/oldest sorting)
"""

from __future__ import annotations

from typing import Any


PROJECTS: list[dict[str, Any]] = [
    {
        "slug": "portfolio-website",
        "title": "Portfolio Website",
        "primary_category": "web",
        "tags": ["flask", "jinja", "bootstrap"],
        "short_description": "A structured portfolio platform built with Flask and Jinja.",
        "full_description": (
            "A portfolio platform designed to showcase Web/Data/Software projects using "
            "a hybrid categorization model (primary_category + tags)."
        ),
        "tech_stack": ["Python", "Flask", "Jinja", "Bootstrap"],
        "links": {
            "repo": "https://github.com/yourname/yourrepo",
            "live": None,
            "demo": None,
        },
        "image": "images/projects/portfolio.png",
        "featured": True,
        "date": "2026-03-01",
    },
    # Add more projects here...
]


def get_all_projects() -> list[dict[str, Any]]:
    """Return a shallow copy of all projects."""
    return list(PROJECTS)


def get_project_by_slug(slug: str) -> dict[str, Any] | None:
    """Find a single project by slug."""
    slug = (slug or "").strip().lower()
    for p in PROJECTS:
        if p.get("slug") == slug:
            return p
    return None