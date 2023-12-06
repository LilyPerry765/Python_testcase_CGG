# --------------------------------------------------------------------------
# Check for due date of periodic invoices.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_due_date.py
# Created at 2020-8-29,  16:36:39
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from jdatetime import datetime as jdatetime

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import Invoice
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.trunk import TrunkService
from cgg.core import api_exceptions
from cgg.core.tools import Tools


def notify_overdue_invoices(
        overdue_invoices,
        notify_type_code,
):
    """
    Notify trunk backend based on notify_type_code
    :param overdue_invoices:
    :type overdue_invoices:
    :param notify_type_code:
    :type notify_type_code:
    :return:
    :rtype:
    """
    notify_object = []
    for overdue_invoice in overdue_invoices:
        if overdue_invoice.subscription.latest_paid_at is None or (
                overdue_invoice.subscription.latest_paid_at and
                overdue_invoice.subscription.latest_paid_at <
                overdue_invoice.created_at
        ):
            notify_object.append({
                "customer_code": str(
                    overdue_invoice.subscription.customer.customer_code,
                ),
                "subscription_code": str(
                    overdue_invoice.subscription.subscription_code
                ),
                "number": str(overdue_invoice.subscription.number),
                'invoice_id': str(overdue_invoice.id),
                'total_cost': str(overdue_invoice.total_cost),
                'cause': Tools.jalali_month_name(
                    jdatetime.fromgregorian(
                        datetime=overdue_invoice.to_date
                    ).month
                ),
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
    help = 'Notify trunk-backend about passed due dates'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[1][0])
    def handle(self, *args, **options):
        due_date_notify = FinanceConfigurations.Invoice.DUE_DATE_NOTIFY
        due_date_warning_two = datetime.now()
        due_date_warning_one = due_date_warning_two + timedelta(days=1)
        due_date_warning_three = due_date_warning_two - timedelta(days=2)
        due_date_warning_four = due_date_warning_two - timedelta(days=14)
        w1_overdue_invoices = Invoice.objects.filter(
            status_code__in=[
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[1][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[3][0],
            ],
            invoice_type_code=FinanceConfigurations.Invoice.TYPES[0][0],
            due_date__lte=due_date_warning_one,
            due_date_notified=due_date_notify[0][0],
        )
        w2_overdue_invoices = Invoice.objects.filter(
            status_code__in=[
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[1][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[3][0],
            ],
            invoice_type_code=FinanceConfigurations.Invoice.TYPES[0][0],
            due_date__lte=due_date_warning_two,
            due_date_notified=due_date_notify[1][0],
        )
        w3_overdue_invoices = Invoice.objects.filter(
            status_code__in=[
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[1][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[3][0],
            ],
            invoice_type_code=FinanceConfigurations.Invoice.TYPES[0][0],
            due_date__lte=due_date_warning_three,
            due_date_notified=due_date_notify[2][0],
        )
        w4_overdue_invoices = Invoice.objects.filter(
            status_code__in=[
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[1][0],
                FinanceConfigurations.Invoice.STATE_CHOICES[3][0],
            ],
            invoice_type_code=FinanceConfigurations.Invoice.TYPES[0][0],
            due_date__lte=due_date_warning_four,
            due_date_notified=due_date_notify[3][0],
        )
        notify_overdue_invoices(
            w1_overdue_invoices,
            FinanceConfigurations.TrunkBackend.Notify.DUE_DATE_WARNING_1,
        )
        notify_overdue_invoices(
            w2_overdue_invoices,
            FinanceConfigurations.TrunkBackend.Notify.DUE_DATE_WARNING_2,
        )
        notify_overdue_invoices(
            w3_overdue_invoices,
            FinanceConfigurations.TrunkBackend.Notify.DUE_DATE_WARNING_3,
        )
        notify_overdue_invoices(
            w4_overdue_invoices,
            FinanceConfigurations.TrunkBackend.Notify.DUE_DATE_WARNING_4,
        )
        w4_overdue_invoices.update(
            due_date_notified=due_date_notify[4][0],
        )
        w3_overdue_invoices.update(
            due_date_notified=due_date_notify[3][0],
        )
        w2_overdue_invoices.update(
            due_date_notified=due_date_notify[2][0],
        )
        w1_overdue_invoices.update(
            due_date_notified=due_date_notify[1][0],
        )
