#!/bin/bash
pipenv run python manage.py finance_import_tariffs ./cgg/apps/finance/management/commands/default_json_files/tariffs.json
echo "Tariffs updated successfully"




