#!/bin/sh
set -e

echo "Running migrations..."
python -c "
from app.app import create_app
from app.models.models import db
app = create_app()
with app.app_context():
    db.create_all()
    try:
        db.session.execute(db.text('ALTER TABLE projects ADD COLUMN featured_order INTEGER'))
        db.session.commit()
    except Exception:
        db.session.rollback()
"

echo "Seeding database..."
python -m app.seed_projects

echo "Starting server..."
exec gunicorn wsgi:app --bind 0.0.0.0:"${PORT:-8000}" --workers 2 --timeout 30
