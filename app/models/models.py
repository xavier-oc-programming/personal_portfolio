"""
models.py

Database objects for the Portfolio Website.

Key responsibilities:
- Create the shared SQLAlchemy instance.
- Define ORM models for the portfolio database.
- Represent the unified project schema in table form.
- Store list-like fields as JSON strings while exposing them
  to Python as normal lists.

Usage:
    from models.models import db, Project
"""

from __future__ import annotations

import json

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
    date = db.Column(db.String(20), nullable=True)

    problem = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)
    results = db.Column(db.Text, nullable=True)

    # Stored in SQLite as JSON strings.
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

        Parameters:
            value (str | None): JSON string stored in the database.

        Returns:
            list[str]: Parsed Python list. Returns an empty list if
            the value is missing or invalid.
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

        Parameters:
            value (list[str] | None): Python list to serialize.

        Returns:
            str: JSON string representation of the list.
        """
        if not value:
            return json.dumps([])

        return json.dumps(value)

    @property
    def tags(self) -> list[str]:
        """
        Return tags as a normal Python list.
        """
        return self._loads_json_list(self.tags_json)

    @tags.setter
    def tags(self, value: list[str] | None) -> None:
        """
        Accept a Python list of tags and store it as JSON text.
        """
        self.tags_json = self._dumps_json_list(value)

    @property
    def tech_stack(self) -> list[str]:
        """
        Return tech_stack as a normal Python list.
        """
        return self._loads_json_list(self.tech_stack_json)

    @tech_stack.setter
    def tech_stack(self, value: list[str] | None) -> None:
        """
        Accept a Python list of tech stack items and store it as JSON text.
        """
        self.tech_stack_json = self._dumps_json_list(value)

    @property
    def screenshots(self) -> list[str]:
        """
        Return screenshots as a normal Python list.
        """
        return self._loads_json_list(self.screenshots_json)

    @screenshots.setter
    def screenshots(self, value: list[str] | None) -> None:
        """
        Accept a Python list of screenshot paths and store it as JSON text.
        """
        self.screenshots_json = self._dumps_json_list(value)

    @property
    def videos(self) -> list[str]:
        """
        Return videos as a normal Python list.
        """
        return self._loads_json_list(self.videos_json)

    @videos.setter
    def videos(self, value: list[str] | None) -> None:
        """
        Accept a Python list of video paths and store it as JSON text.
        """
        self.videos_json = self._dumps_json_list(value)

    @property
    def links(self) -> dict[str, str | None]:
        """
        Compatibility helper for existing templates.

        Returns:
            dict[str, str | None]: Repo/live/demo links in the same
            structure used by the Phase 2 in-memory dataset.
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

        Returns:
            dict[str, Any]: Media structure matching the earlier
            in-memory project schema.
        """
        return {
            "card_image": self.card_image,
            "screenshots": self.screenshots,
            "videos": self.videos,
        }