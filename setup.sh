#!/bin/bash

# Update pip and setuptools
pip install --upgrade pip setuptools

# Install dependencies from requirements.txt
pip install --no-cache-dir -r requirements.txt

# Run Django migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files (if applicable)
python manage.py collectstatic --noinput