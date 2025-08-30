#!/usr/bin/env bash
set -e  # Exit on any error

echo "=== Installing Poetry ==="
# Install Poetry if not available
if ! command -v poetry &> /dev/null
then
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

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

echo "=== Linking React build into Django static folder ==="
DJANGO_STATIC_ROOT="projectRoot/static"
rm -rf $DJANGO_STATIC_ROOT/frontend
cp -r frontend/build $DJANGO_STATIC_ROOT/frontend

echo "=== Collecting Django static files ==="
poetry run python manage.py collectstatic --noinput

echo "=== Build complete ==="
