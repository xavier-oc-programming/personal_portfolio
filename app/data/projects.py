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
- media (dict)
    - card_image (optional: path string)
    - screenshots (list[str])
    - videos (list[str])
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
        "short_description": "Flask + Jinja portfolio with reusable components and clean architecture.",
        "full_description": (
            "A portfolio platform designed to showcase Web, Data, and Software projects "
            "using a hybrid categorization model built around a primary category and tags."
        ),
        "tech_stack": ["Python", "Flask", "Jinja", "Bootstrap"],
        "links": {
            "repo": "https://github.com/xavier-oc-programming/personal_portfolio",
            "live": None,
            "demo": None,
        },
        "media": {
            "card_image": None,
            "screenshots": [],
            "videos": [],
        },
        "featured": True,
        "date": "2026-03-01",
        "problem": (
            "The project needed a structured way to present work across different technical areas "
            "without creating a confusing or inconsistent user experience."
        ),
        "solution": (
            "I designed a Flask-based portfolio with reusable templates, a shared data schema, "
            "and a project hub that can later evolve into a database-driven system."
        ),
        "challenges": (
            "A major challenge was deciding how to organize projects that overlap across Web, Data, "
            "and Software while keeping the site architecture simple and scalable."
        ),
        "results": (
            "The result is a clean MVP portfolio foundation that supports dynamic rendering, "
            "consistent layout, and future expansion into richer project detail pages."
        ),
    },
    {
        "slug": "morse-code-converter",
        "title": "Morse Code Converter",
        "primary_category": "software",
        "tags": ["python", "cli"],
        "short_description": "CLI application converting text to Morse code with clean modular structure.",
        "full_description": (
            "A Python command-line tool that converts standard text input into Morse code output "
            "with a simple interface and readable program structure."
        ),
        "tech_stack": ["Python"],
        "links": {
            "repo": None,
            "live": None,
            "demo": None,
        },
        "media": {
            "card_image": "images/projects/morse-code-converter/card/morse_code.png",
            "screenshots": [],
            "videos": [],
        },
        "featured": True,
        "date": "2026-02-20",
        "problem": "Convert user text into Morse code accurately in a clean CLI application.",
        "solution": "Built a modular Python script that maps characters to Morse output.",
        "challenges": "Handling formatting and keeping the code clean and readable.",
        "results": "Produced a working converter that demonstrates Python fundamentals and structure.",
    },
    {
        "slug": "data-project-placeholder",
        "title": "Data Project Placeholder",
        "primary_category": "data",
        "tags": ["pandas", "data-viz"],
        "short_description": "A data analysis project using Python, Pandas, and visualization.",
        "full_description": (
            "Placeholder entry representing the type of structured data project that will appear "
            "in the portfolio as the dataset grows."
        ),
        "tech_stack": ["Python", "Pandas", "Matplotlib"],
        "links": {
            "repo": None,
            "live": None,
            "demo": None,
        },
        "media": {
            "card_image": None,
            "screenshots": [],
            "videos": [],
        },
        "featured": False,
        "date": "2026-02-10",
        "problem": "Analyze a dataset and communicate insights clearly.",
        "solution": "Use Python and Pandas for transformation, then visualize key patterns.",
        "challenges": "Ensuring clarity, structure, and readable outputs.",
        "results": "A placeholder for future portfolio-ready data analysis work.",
    },
]


def get_all_projects() -> list[dict[str, Any]]:
    """Return a shallow copy of all projects."""
    return list(PROJECTS)


def get_project_by_slug(slug: str) -> dict[str, Any] | None:
    """Find a single project by slug."""
    normalized_slug = (slug or "").strip().lower()

    for project in PROJECTS:
        if project.get("slug") == normalized_slug:
            return project

    return None