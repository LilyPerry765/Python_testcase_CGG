# --------------------------------------------------------------------------
# Issue periodic invoices for Postpaid and Prepaid subscriptions, leaving
# out Unlimited ones.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_periodic_invoice.py
# Created at 2020-8-29,  16:42:27
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from datetime import datetime

import pytz
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from jdatetime import datetime as jdatetime, timedelta as jtimedelta

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import Subscription
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.invoice import (
    InvoiceService,
)
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.trunk import TrunkService
from cgg.core import api_exceptions


class Command(BaseCommand):
    help = 'Issue periodic invoices'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[0][0])
    def handle(self, *args, **options):
        today_jalali = jdatetime.now(tz=pytz.timezone("Asia/Tehran"))
        start_command_datetime = datetime.now()
        # RuntimeConfig for this value is @deprecated
        if today_jalali.day == 1:
            self.stdout.write(
                "issuing periodic invoices ..."
            )
            jalali_year = today_jalali.year
            jalali_month = today_jalali.month
            if jalali_month == 1:
                jalali_year -= 1
                jalali_month = 12
                # This is for further usage to check if the year is leap
                today_jalali = today_jalali - jtimedelta(days=32)
            else:
                jalali_month -= 1
            if 1 <= jalali_month <= 6:
                jalali_day = 31
            else:
                jalali_day = 30
                if jalali_month == 12 and not today_jalali.isleap():
                    jalali_day = 29

            from_date_jalali = jdatetime(
                year=jalali_year,
                month=jalali_month,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=pytz.timezone("Asia/Tehran"),
            )
            to_date_jalali = jdatetime(
                year=jalali_year,
                month=jalali_month,
                day=jalali_day,
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
                tzinfo=pytz.timezone("Asia/Tehran"),
            )
            from_date_tz = from_date_jalali.togregorian().astimezone(pytz.UTC)
            to_date_tz = to_date_jalali.togregorian().astimezone(pytz.UTC)
            from_date = datetime(
                year=from_date_tz.year,
                month=from_date_tz.month,
                day=from_date_tz.day,
                hour=from_date_tz.hour,
                minute=from_date_tz.minute,
                second=from_date_tz.second,
                microsecond=from_date_tz.microsecond,
            )
            to_date = datetime(
                year=to_date_tz.year,
                month=to_date_tz.month,
                day=to_date_tz.day,
                hour=to_date_tz.hour,
                minute=to_date_tz.minute,
                second=to_date_tz.second,
                microsecond=to_date_tz.microsecond,
            )
            subscriptions_object = Subscription.objects.filter(
                is_allocated=True,
                subscription_type__in=[
                    FinanceConfigurations.Subscription.TYPE[0][0],
                    FinanceConfigurations.Subscription.TYPE[1][0],
                ]
            )
            for subscription_object in subscriptions_object:
                try:
                    InvoiceService.issue_periodic_invoice(
                        subscription_object.id,
                        from_date,
                        to_date,
                        description=_(
                            "This invoice a generated automatically at the "
                            "end of the period",
                        )
                    )
                except Exception as e:
                    JobService.add_failed_job(
                        FinanceConfigurations.Jobs.TYPES[0][0],
                        'v1',
                        'InvoiceService',
                        'issue_periodic_invoice',
                        json.dumps({
                            "subscription_id": str(subscription_object.id),
                            "from_date": str(from_date.timestamp()),
                            "to_date": str(to_date.timestamp()),
                            "notify_singular": True,
                            "description": _(
                                "This invoice a generated automatically at "
                                "the end of the period",
                            )
                        }),
                        str(e)
                    )

            self.stdout.write(
                "issuing periodic invoices completed successfully!"
            )
            self.stdout.write(
                "notifying customers about periodic invoices ..."
            )
            subscription_objects = Subscription.objects.distinct().filter(
                invoices__to_date__exact=to_date,
                invoices__created_at__gte=start_command_datetime
            )

            notify_object = []
            notify_type = FinanceConfigurations.TrunkBackend.Notify \
                .PERIODIC_INVOICE
            for subscription_object in subscription_objects:
                latest_invoice = subscription_object.invoices.latest(
                    'created_at',
                )
                notify_object.append({
                    "customer_code":
                        str(subscription_object.customer.customer_code),
                    "subscription_code":
                        str(subscription_object.subscription_code),
                    "number": str(subscription_object.number),
                    'invoice_id': str(latest_invoice.id),
                    'total_cost': str(latest_invoice.total_cost),
                    'auto_payed': True if
                    latest_invoice.status_code ==
                    FinanceConfigurations.Invoice.STATE_CHOICES[2][
                        0] else False,
                })
                # Notify 25 objects at a time
                if len(notify_object) == 25:
                    try:
                        TrunkService.notify_trunk_backend(
                            notify_type_code=notify_type,
                            notify_object=notify_object,
                        )
                    except api_exceptions.APIException as e:
                        JobService.add_failed_job(
                            FinanceConfigurations.Jobs.TYPES[1][0],
                            'v1',
                            'TrunkService',
                            'notify_trunk_backend',
                            json.dumps({
                                "notify_type_code": notify_type,
                                "notify_object": notify_object,
                            }),
                            str(e)
                        )
                    notify_object = []

            # Notify the rest of invoices (less than 25)
            if notify_object:
                try:
                    TrunkService.notify_trunk_backend(
                        notify_type_code=notify_type,
                        notify_object=notify_object,
                    )
                except api_exceptions.APIException as e:
                    JobService.add_failed_job(
                        FinanceConfigurations.Jobs.TYPES[1][0],
                        'v1',
                        'TrunkService',
                        'notify_trunk_backend',
                        json.dumps({
                            "notify_type_code": notify_type,
                            "notify_object": notify_object,
                        }),
                        str(e)
                    )
            self.stdout.write(
                "notifying customers about periodic invoices completed "
                "successfully!"
            )
