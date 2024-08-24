#!/bin/bash

pip install setuptools
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate