# --------------------------------------------------------------------------
# Redo failed jobs.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_failed_jobs.py
# Created at 2020-8-29,  16:37:35
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.core.management.base import BaseCommand

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import FailedJob
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.job import JobService


class Command(BaseCommand):
    help = 'Redo failed jobs and update status'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[2][0])
    def handle(self, *args, **options):
        failed_job_objects = FailedJob.objects.filter(
            is_done=False
        )
        for failed_job_object in failed_job_objects:
            JobService.redo_the_job(failed_job_object)
