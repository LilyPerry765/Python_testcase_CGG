#!/bin/bash
pipenv run python manage.py compilemessages  && \
pipenv run python manage.py makemigrations && \
pipenv run python manage.py migrate --database=default && \
pipenv run python manage.py migrate --database=log && \
pipenv run python manage.py loaddata tax && \
pipenv run python manage.py loaddata packages  && \
pipenv run python manage.py collectstatic --noinput  && \
pipenv run python manage.py createsuperuser && \
pipenv run python manage.py finance_init_cgrates  && \
pipenv run python manage.py finance_import_destinations ./cgg/apps/finance/management/commands/default_json_files/destinations.json  && \
pipenv run python manage.py finance_import_branches ./cgg/apps/finance/management/commands/default_json_files/branches.json && \
pipenv run python manage.py finance_update_runtime_config && \
pipenv run python manage.py finance_import_tariffs ./cgg/apps/finance/management/commands/default_json_files/tariffs.json
echo "CGG installed successfully"
