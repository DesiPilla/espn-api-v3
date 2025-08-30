#!/usr/bin/env bash
set -e  # Exit on any error

echo "=== Installing Poetry 1.8.5 ==="
# Install Poetry version 1.8.5
export POETRY_VERSION=1.8.5
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

echo "=== Setting up Python environment with Poetry ==="
# Install Python dependencies without installing the project itself
poetry install --no-root

echo "=== Installing Node.js ==="
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

echo "=== Building React frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Collecting Django static files ==="
poetry run python manage.py collectstatic --noinput

echo "=== Build complete ==="
