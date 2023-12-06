# --------------------------------------------------------------------------
# Check for created at of periodic invoices for deallocation.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_due_date.py
# Created at 2020-9-27,  11:36:39
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import Subscription
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.runtime_config import (
    RuntimeConfigService,
)
from cgg.apps.finance.versions.v1.services.trunk import TrunkService
from cgg.core import api_exceptions


def notify_overdue_subscriptions(
        overdue_subscriptions,
        notify_type_code,
):
    """
    Notify trunk backend based on notify_type_code
    :param overdue_subscriptions:
    :type overdue_subscriptions:
    :param notify_type_code:
    :type notify_type_code:
    :return:
    :rtype:
    """
    notify_object = []
    for overdue_subscription in overdue_subscriptions:
        notify_object.append({
            "customer_code": str(
                overdue_subscription.customer.customer_code,
            ),
            "subscription_code": str(
                overdue_subscription.subscription_code
            ),
            "number": str(overdue_subscription.number),
        })

        # Send 25 invoice at a time
        if len(notify_object) == 25:
            try:
                TrunkService.notify_trunk_backend(
                    notify_type_code=notify_type_code,
                    notify_object=notify_object,
                )
            except api_exceptions.APIException as e:
                JobService.add_failed_job(
                    FinanceConfigurations.Jobs.TYPES[1][0],
                    'v1',
                    'TrunkService',
                    'notify_trunk_backend',
                    json.dumps({
                        "notify_type_code": notify_type_code,
                        "notify_object": notify_object,
                    }),
                    str(e)
                )
            notify_object = []

    # Send the rest of invoices
    if notify_object:
        try:
            TrunkService.notify_trunk_backend(
                notify_type_code=notify_type_code,
                notify_object=notify_object,
            )
        except api_exceptions.APIException as e:
            JobService.add_failed_job(
                FinanceConfigurations.Jobs.TYPES[1][0],
                'v1',
                'TrunkService',
                'notify_trunk_backend',
                json.dumps({
                    "notify_type_code": notify_type_code,
                    "notify_object": notify_object,
                }),
                str(e)
            )


class Command(BaseCommand):
    help = 'Notify trunk-backend about deallocation'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[13][0])
    def handle(self, *args, **options):
        deallocation_due = int(
            RuntimeConfigService.get_value(
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[6][0],
            )
        )
        datetime_due = datetime.now() - timedelta(days=deallocation_due)
        datetime_warning = datetime_due + timedelta(days=2)
        warn_subscriptions = Subscription.objects.filter(
            Q(
                is_allocated=True,
                latest_paid_at__lt=datetime_warning,
                deallocate_warned=False,
            ) |
            Q(
                is_allocated=True,
                latest_paid_at__isnull=True,
                created_at__lt=datetime_warning,
                deallocate_warned=False,
            )
        )
        overdue_subscriptions = Subscription.objects.filter(
            Q(
                is_allocated=True,
                latest_paid_at__lt=datetime_due,
                deallocate_warned=True,
            ) |
            Q(
                is_allocated=True,
                latest_paid_at__isnull=True,
                created_at__lt=datetime_due,
                deallocate_warned=True,
            )
        )
        notify_overdue_subscriptions(
            warn_subscriptions,
            FinanceConfigurations.TrunkBackend.Notify.DEALLOCATION_WARNING_1,
        )
        notify_overdue_subscriptions(
            overdue_subscriptions,
            FinanceConfigurations.TrunkBackend.Notify.DEALLOCATION_WARNING_2,
        )
        warn_subscriptions.update(
            deallocate_warned=True,
        )
