# --------------------------------------------------------------------------
# Check for loose channels (sessions) in CGRateS and remove them.
# (C) 2021 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_check_loose_sessions.py
# Created at 2021-1-26,  10:25:22
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations


class Command(BaseCommand):
    help = 'Check for loose channels system-wide and disconnect them if needed'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[15][0])
    def handle(self, *args, **options):
        BasicService.disconnect_sessions(
            "",
            setup_time=datetime.now() - timedelta(
                seconds=int(settings.CGG['MAX_CALL_DURATION'])
            )
        )
