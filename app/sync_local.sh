#!/bin/bash
# Pull latest changes from GitHub and reseed the local SQLite database.
# Run from repo root: bash app/sync_local.sh

set -e

git pull --rebase
python -m app.local_seed
