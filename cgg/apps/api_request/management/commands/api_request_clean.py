# --------------------------------------------------------------------------
# Clean log database from old api requests
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - api_request_clean.py
# Created at 2020-10-18,  14:40:7
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from cgg.apps.api_request.models import APIRequest
from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations


class Command(BaseCommand):
    help = 'Clean api_request table from log database'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[14][0])
    def handle(self, *args, **options):
        days = settings.CGG['API_REQUESTS_KEEP_DAYS']
        older_than = datetime.now() - timedelta(days=days)
        APIRequest.objects.filter(
            created_at__lte=older_than,
        ).delete()
