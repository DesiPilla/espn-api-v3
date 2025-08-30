#!/bin/bash

# Exit on error
set -o errexit  

# Upgrade pip and install Poetry
python -m pip install --upgrade pip
pip install poetry

# Export dependencies to requirements.txt for Railway
poetry export -f requirements.txt --without-hashes -o requirements.txt

# Install Python dependencies
pip install -r requirements.txt

# Build React frontend
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Copy React build files to Django static folder
cp -r frontend/build/* backend/static/

# Run Django collectstatic
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
