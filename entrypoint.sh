#!/bin/sh
set -e

echo "Seeding database..."
python -m app.seed_projects

echo "Starting server..."
exec gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 2 --preload
