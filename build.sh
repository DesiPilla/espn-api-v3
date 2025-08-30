#!/bin/bash
set -e  # exit on any error

# Build frontend
cd frontend
npm ci
npm run build
cd ..

# Collect static files for Django
python manage.py collectstatic --noinput
