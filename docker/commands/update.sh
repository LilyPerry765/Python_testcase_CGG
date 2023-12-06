#!/bin/bash
pipenv run python manage.py compilemessages && \
pipenv run python manage.py makemigrations && \
pipenv run python manage.py migrate --database=default && \
pipenv run python manage.py migrate --database=log  && \
pipenv run python manage.py finance_update_runtime_config
echo "CGG updated successfully"
