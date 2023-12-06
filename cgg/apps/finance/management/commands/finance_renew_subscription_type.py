# --------------------------------------------------------------------------
# Renew subscription's type based on number. Use it when a new prefix
# defined in RuntimeConfigs.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_renew_subscription_type.py
# Created at 2020-8-29,  16:43:10
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

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[9][0])
    def handle(self, *args, **options):
        subscription_objects = Subscription.objects.filter(
            is_allocated=True,
        )
        count = 0
        for subscription_object in subscription_objects:
            try:
                SubscriptionService.renew_subscription_type(
                    subscription_id=subscription_object.id
                )
                count += 1
            except api_exceptions.APIException as e:
                JobService.add_failed_job(
                    FinanceConfigurations.Jobs.TYPES[3][0],
                    'v1',
                    'SubscriptionService',
                    'renew_subscription_type',
                    json.dumps({
                        "subscription_id": subscription_object.id
                    }),
                    str(e)
                )

        self.stdout.write(
            f"{count} subscriptions renewed",
        )
