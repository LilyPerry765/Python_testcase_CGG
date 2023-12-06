# --------------------------------------------------------------------------
# Renew branches based on RuntimeConfigs and Branches
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_renew_branches.py
# Created at 2020-8-29,  16:36:1
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json

from django.core.management.base import BaseCommand

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import Subscription
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.subscription import (
    SubscriptionService,
)
from cgg.core import api_exceptions


class Command(BaseCommand):
    help = "Renew subscription branches based on branch's prefix " \
           "and subscription's number"

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[3][0])
    def handle(self, *args, **options):
        subscription_objects = Subscription.objects.all()
        for subscription_object in subscription_objects:
            try:
                SubscriptionService.renew_branch(
                    subscription_id=subscription_object.id
                )
            except api_exceptions.APIException as e:
                JobService.add_failed_job(
                    FinanceConfigurations.Jobs.TYPES[2][0],
                    'v1',
                    'SubscriptionService',
                    'renew_branch',
                    json.dumps({
                        "subscription_id": subscription_object.id
                    }),
                    str(e)
                )
