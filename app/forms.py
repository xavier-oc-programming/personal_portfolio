"""
forms.py

Form definitions for the Portfolio Website.

Key responsibilities:
- Define Flask-WTF forms used by the application.
- Centralize field structure and validation rules.
- Provide CSRF-protected form handling through Flask-WTF.

Usage:
    from forms import ContactForm
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 60

MAX_EMAIL_LENGTH = 254

MIN_MESSAGE_LENGTH = 10
MAX_MESSAGE_LENGTH = 2000


class ContactForm(FlaskForm):
    """
    Contact form used on the portfolio contact page.
    """

    company = StringField(
        "Company",
        validators=[Optional()],
        render_kw={
            "class": "form-control",
            "autocomplete": "off",
            "tabindex": "-1",
        },
    )

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Name is required."),
            Length(
                min=MIN_NAME_LENGTH,
                max=MAX_NAME_LENGTH,
                message=f"Name must be between {MIN_NAME_LENGTH} and {MAX_NAME_LENGTH} characters.",
            ),
        ],
        render_kw={
            "class": "form-control",
            "autocomplete": "name",
            "minlength": MIN_NAME_LENGTH,
            "maxlength": MAX_NAME_LENGTH,
        },
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
            Length(
                max=MAX_EMAIL_LENGTH,
                message=f"Email must be {MAX_EMAIL_LENGTH} characters or fewer.",
            ),
        ],
        render_kw={
            "class": "form-control",
            "autocomplete": "email",
            "inputmode": "email",
            "maxlength": MAX_EMAIL_LENGTH,
        },
    )

    message = TextAreaField(
        "Message",
        validators=[
            DataRequired(message="Message is required."),
            Length(
                min=MIN_MESSAGE_LENGTH,
                max=MAX_MESSAGE_LENGTH,
                message=f"Message must be between {MIN_MESSAGE_LENGTH} and {MAX_MESSAGE_LENGTH} characters.",
            ),
        ],
        render_kw={
            "class": "form-control",
            "rows": 6,
            "minlength": MIN_MESSAGE_LENGTH,
            "maxlength": MAX_MESSAGE_LENGTH,
        },
    )

    submit = SubmitField(
        "Send Message",
        render_kw={
            "class": "btn btn-dark",
        },
    )