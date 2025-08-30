#!/usr/bin/env bash
set -e  # Exit on any error

echo "=== Setting up Python environment with Poetry ==="
# Install dependencies
poetry install --no-root

echo "=== Building React frontend ==="
# Navigate to frontend folder and install dependencies
cd frontend
npm install
npm run build
cd ..

echo "=== Collecting static files for Django ==="
# Make sure Django knows where static files are
poetry run python manage.py collectstatic --noinput

echo "=== Build complete ==="
