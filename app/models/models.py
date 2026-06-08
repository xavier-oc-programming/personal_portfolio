"""
models.py

Database objects for the Portfolio Website.

Key responsibilities:
- Create the shared SQLAlchemy instance.
- Define ORM models for the portfolio database.
- Represent the unified project schema in table form.
- Store list-like fields as JSON strings while exposing them
  to Python as normal lists.
- Persist contact form submissions for the portfolio site.

Usage:
    from models.models import db, Project, ContactMessage
"""

from __future__ import annotations

import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Project(db.Model):
    """
    ORM model representing a single portfolio project.

    This table mirrors the unified project schema used in earlier
    phases of the portfolio. List-like fields such as tags and
    tech_stack are stored in the database as JSON strings, while
    Python code can interact with them as normal lists.
    """

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    primary_category = db.Column(db.String(50), nullable=False)

    short_description = db.Column(db.String(300), nullable=False)
    full_description = db.Column(db.Text, nullable=False)

    featured = db.Column(db.Boolean, default=False, nullable=False)
    featured_order = db.Column(db.Integer, nullable=True)
    loading_warning = db.Column(db.Boolean, default=False, nullable=False)
    date = db.Column(db.String(20), nullable=True)

    problem = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)
    results = db.Column(db.Text, nullable=True)

    tags_json = db.Column("tags", db.Text, nullable=True)
    tech_stack_json = db.Column("tech_stack", db.Text, nullable=True)
    screenshots_json = db.Column("screenshots", db.Text, nullable=True)
    videos_json = db.Column("videos", db.Text, nullable=True)

    repo_url = db.Column(db.String(255), nullable=True)
    live_url = db.Column(db.String(255), nullable=True)
    demo_url = db.Column(db.String(255), nullable=True)

    card_image = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        """
        Developer-friendly string representation of a Project instance.
        """
        return f"<Project id={self.id} slug='{self.slug}' title='{self.title}'>"

    @staticmethod
    def _loads_json_list(value: str | None) -> list[str]:
        """
        Convert a JSON string from the database into a Python list.
        """
        if not value:
            return []

        try:
            parsed_value = json.loads(value)

            if isinstance(parsed_value, list):
                return parsed_value

            return []
        except (TypeError, json.JSONDecodeError):
            return []

    @staticmethod
    def _dumps_json_list(value: list[str] | None) -> str:
        """
        Convert a Python list into a JSON string for database storage.
        """
        if not value:
            return json.dumps([])

        return json.dumps(value)

    @property
    def tags(self) -> list[str]:
        """Return tags as a normal Python list."""
        return self._loads_json_list(self.tags_json)

    @tags.setter
    def tags(self, value: list[str] | None) -> None:
        """Accept a Python list of tags and store it as JSON text."""
        self.tags_json = self._dumps_json_list(value)

    @property
    def tech_stack(self) -> list[str]:
        """Return tech_stack as a normal Python list."""
        return self._loads_json_list(self.tech_stack_json)

    @tech_stack.setter
    def tech_stack(self, value: list[str] | None) -> None:
        """Accept a Python list of tech stack items and store it as JSON text."""
        self.tech_stack_json = self._dumps_json_list(value)

    @property
    def screenshots(self) -> list[str]:
        """Return screenshots as a normal Python list."""
        return self._loads_json_list(self.screenshots_json)

    @screenshots.setter
    def screenshots(self, value: list[str] | None) -> None:
        """Accept a Python list of screenshot paths and store it as JSON text."""
        self.screenshots_json = self._dumps_json_list(value)

    @property
    def videos(self) -> list[str]:
        """Return videos as a normal Python list."""
        return self._loads_json_list(self.videos_json)

    @videos.setter
    def videos(self, value: list[str] | None) -> None:
        """Accept a Python list of video paths and store it as JSON text."""
        self.videos_json = self._dumps_json_list(value)

    @property
    def links(self) -> dict[str, str | None]:
        """
        Compatibility helper for existing templates.
        """
        return {
            "repo": self.repo_url,
            "live": self.live_url,
            "demo": self.demo_url,
        }

    @property
    def media(self) -> dict[str, str | list[str] | None]:
        """
        Compatibility helper for existing templates.
        """
        return {
            "card_image": self.card_image,
            "screenshots": self.screenshots,
            "videos": self.videos,
        }

    def to_dict(self) -> dict:
        """
        Serialise this project to a plain dictionary for API responses.

        Only public-facing fields are included. Internal IDs are omitted.
        """
        return {
            "title": self.title,
            "slug": self.slug,
            "summary": self.short_description,
            "description": self.full_description,
            "category": self.primary_category,
            "tags": self.tags,
            "tech_stack": self.tech_stack,
            "github_url": self.repo_url,
            "live_url": self.live_url,
            "demo_url": self.demo_url,
            "featured": self.featured,
            "loading_warning": self.loading_warning,
            "card_image": self.card_image,
            "screenshots": self.screenshots,
            "videos": self.videos,
            "date": self.date,
            "problem": self.problem,
            "solution": self.solution,
            "challenges": self.challenges,
            "results": self.results,
        }


class ContactMessage(db.Model):
    """
    ORM model representing a contact form submission.

    This table stores messages submitted through the portfolio's
    contact page so they persist in the SQLite database.
    """

    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        """
        Developer-friendly string representation of a ContactMessage instance.
        """
        return f"<ContactMessage id={self.id} email='{self.email}'>"