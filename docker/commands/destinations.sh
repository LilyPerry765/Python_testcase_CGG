#!/bin/bash
pipenv run python manage.py finance_import_destinations ./cgg/apps/finance/management/commands/default_json_files/destinations.json
echo "Destinations updated successfully"




