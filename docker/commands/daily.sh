#!/bin/bash
pipenv run python manage.py finance_periodic_invoice
pipenv run python manage.py finance_integrity_check
pipenv run python manage.py api_request_clean
