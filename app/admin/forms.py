"""
app/admin/forms.py

Forms for the admin panel.
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, MultipleFileField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL


ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "webp"]
ALLOWED_VIDEO_EXTENSIONS = ["mp4", "webm", "mov"]


class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    slug = StringField("Slug", validators=[DataRequired(), Length(max=100)])
    primary_category = SelectField(
        "Category",
        choices=[("web", "Web"), ("data", "Data"), ("software", "Software"), ("ai-ml", "AI / ML")],
        validators=[DataRequired()],
    )
    short_description = StringField(
        "Short Description", validators=[DataRequired(), Length(max=300)]
    )
    full_description = TextAreaField("Full Description", validators=[DataRequired()])
    featured = BooleanField("Featured")
    loading_warning = BooleanField("Loading Warning")
    date = StringField("Date (YYYY-MM-DD)", validators=[Optional(), Length(max=20)])
    problem = TextAreaField("Problem", validators=[Optional()])
    solution = TextAreaField("Solution", validators=[Optional()])
    challenges = TextAreaField("Challenges", validators=[Optional()])
    results = TextAreaField("Results", validators=[Optional()])
    tags = StringField("Tags (comma-separated)", validators=[Optional()])
    tech_stack = StringField("Tech Stack (comma-separated)", validators=[Optional()])
    repo_url = StringField("Repo URL", validators=[Optional(), URL(), Length(max=255)])
    live_url = StringField("Live URL", validators=[Optional(), URL(), Length(max=255)])
    demo_url = StringField("Demo URL", validators=[Optional(), URL(), Length(max=255)])
    submit = SubmitField("Save Project")


class CardImageForm(FlaskForm):
    card_image = FileField(
        "Card Image",
        validators=[FileAllowed(ALLOWED_IMAGE_EXTENSIONS, "Images only (jpg, png, gif, webp).")],
    )
    submit = SubmitField("Upload Card Image")


class ScreenshotForm(FlaskForm):
    screenshots = MultipleFileField(
        "Screenshots",
        validators=[FileAllowed(ALLOWED_IMAGE_EXTENSIONS, "Images only (jpg, png, gif, webp).")],
    )
    submit = SubmitField("Upload Screenshots")


class VideoForm(FlaskForm):
    video = FileField(
        "Video",
        validators=[FileAllowed(ALLOWED_VIDEO_EXTENSIONS, "Videos only (mp4, webm, mov).")],
    )
    submit = SubmitField("Upload Video")


class YouTubeForm(FlaskForm):
    youtube_url = StringField(
        "YouTube URL",
        validators=[DataRequired(), URL(), Length(max=255)],
    )
    submit = SubmitField("Add YouTube Video")
