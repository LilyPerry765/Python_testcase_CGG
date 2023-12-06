# --------------------------------------------------------------------------
# Handle received notification from CGRateS
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - cgrates_notify.py
# Created at 2020-8-29,  16:55:9
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import logging
from datetime import datetime, timedelta

import math
from celery import shared_task
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions,
)
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.invoice import (
    InvoiceService,
)
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.package_invoice import (
    PackageInvoiceService,
)
from cgg.apps.finance.versions.v1.services.trunk import TrunkService
from cgg.core import api_exceptions

logger = logging.getLogger('common')

TB_NOTIFY = FinanceConfigurations.TrunkBackend.Notify


@shared_task
def handle_cgrates_notification(
        notify_type,
        body,
):
    """
    Handle CGRateS Notification using celery
    :param notify_type:
    :param body:
    :return:
    """
    CGRateSNotifyService.cgrates_notification(
        notify_type,
        body,
    )


@shared_task
def handle_cgrates_expired_notification(
        subscription_code
):
    """
    Handle CGRateS Notification for prepaid expiry using celery
    :param subscription_code:
    :return:
    """
    CGRateSNotifyService.expiry_notification(
        subscription_code,
    )


@shared_task
def handle_max_usage_postpaid_invoice(
        subscription_code,
):
    """
    Issue an interim invoice if necessary and notify trunk backend using celery
    :param subscription_code:
    :type subscription_code:
    :return:
    :rtype:
    """
    InvoiceService.issue_interim_invoice(
        subscription_code=subscription_code,
        description=_(
            'This invoice a generated automatically because '
            'of 100 percent usage of base balance',
        ),
        bypass_type=FinanceConfigurations.Invoice.BypassType.MAX_USAGE,
    )


class CGRateSNotifyService:

    @classmethod
    def cgrates_notification(cls, notify_type, body):
        """
        Directly related to CGRateS
        :param notify_type: from url to decide about type of notifications
        :param body: comes directly from CGRateS call_url_async action for
        """
        account_object = BasicService.account_object(body)
        subscription_code = CGRatesConventions.revert_account_name(
            original_name=account_object['id'],
            with_tenant=True,
        )
        subscription_object = CommonService.get_subscription_object(
            customer_code=None,
            subscription_code=subscription_code,
        )
        number = subscription_object.number
        customer_code = subscription_object.customer.customer_code
        branch_code = subscription_object.branch.branch_code

        if notify_type == FinanceConfigurations.Notify.PostpaidEightyPercent:
            if InvoiceService.verify_and_repair(
                    branch_code=branch_code,
                    subscription_code=subscription_code,
            ):
                InvoiceService.issue_interim_invoice(
                    subscription_code=subscription_code,
                    description=_(
                        'This invoice a generated automatically because '
                        'of 80 percent usage of base balance'
                    ),
                    bypass_type=
                    FinanceConfigurations.Invoice.BypassType.EIGHTY_PERCENT,
                )
        elif notify_type == FinanceConfigurations.Notify.PostpaidMaxUsage:
            if InvoiceService.verify_and_repair(
                    branch_code=branch_code,
                    subscription_code=subscription_code,
                    max_usage=True,
            ):
                notify_object = {
                    "customer_code": customer_code,
                    "subscription_code": subscription_code,
                    "number": number,
                }
                try:
                    TrunkService.notify_trunk_backend(
                        notify_type_code=TB_NOTIFY.POSTPAID_MAX_USAGE,
                        notify_object=notify_object,
                    )
                except api_exceptions.APIException as e:
                    JobService.add_failed_job(
                        FinanceConfigurations.Jobs.TYPES[1][0],
                        'v1',
                        'TrunkService',
                        'notify_trunk_backend',
                        json.dumps({
                            "notify_type_code": TB_NOTIFY.POSTPAID_MAX_USAGE,
                            "notify_object": notify_object,
                        }),
                        str(e)
                    )
                wait_in_minutes = math.ceil(
                    float(BasicService.get_branch_maximum_rate(
                        branch_code
                    )) / float(BasicService.get_branch_minimum_rate(
                        branch_code
                    ))
                )
                check_time = datetime.now() + timedelta(
                    minutes=wait_in_minutes
                )
                handle_max_usage_postpaid_invoice.apply_async(
                    args=(
                        subscription_code,
                    ),
                    eta=check_time,
                )
        elif notify_type == FinanceConfigurations.Notify.PrepaidEightyPercent:
            if InvoiceService.verify_and_repair(
                    branch_code=branch_code,
                    subscription_code=subscription_code,
                    is_prepaid=True,
            ):
                notify_object = {
                    "subscription_code": subscription_code,
                    "customer_code": customer_code,
                    "number": number,
                }
                try:
                    TrunkService.notify_trunk_backend(
                        notify_type_code=TB_NOTIFY.PREPAID_EIGHTY_PERCENT,
                        notify_object=notify_object,
                    )
                except api_exceptions.APIException as e:
                    JobService.add_failed_job(
                        FinanceConfigurations.Jobs.TYPES[1][0],
                        'v1',
                        'TrunkService',
                        'notify_trunk_backend',
                        json.dumps({
                            "notify_type_code":
                                TB_NOTIFY.PREPAID_EIGHTY_PERCENT,
                            "notify_object": notify_object,
                        }),
                        str(e),
                    )
        elif notify_type == FinanceConfigurations.Notify.PrepaidMaxUsage:
            if InvoiceService.verify_and_repair(
                    branch_code=branch_code,
                    subscription_code=subscription_code,
                    max_usage=True,
                    is_prepaid=True,
            ):
                is_renewed = PackageInvoiceService.expire_prepaid(
                    subscription_code,
                )
                notify_object = {
                    "customer_code": customer_code,
                    "subscription_code": subscription_code,
                    "number": number,
                }
                tb_notify_type = TB_NOTIFY.PREPAID_MAX_USAGE
                if is_renewed:
                    tb_notify_type = TB_NOTIFY.PREPAID_RENEWED
                try:
                    TrunkService.notify_trunk_backend(
                        notify_type_code=tb_notify_type,
                        notify_object=notify_object,
                    )
                except api_exceptions.APIException as e:
                    JobService.add_failed_job(
                        FinanceConfigurations.Jobs.TYPES[1][0],
                        'v1',
                        'TrunkService',
                        'notify_trunk_backend',
                        json.dumps({
                            "notify_type_code": tb_notify_type,
                            "notify_object": notify_object,
                        }),
                        str(e),
                    )

    @classmethod
    def expiry_notification(cls, subscription_code):
        """
        Get the expiry notification from CGRateS and handle it based on renewal
        :param subscription_code:
        :return:
        """
        # Prepaid expired
        is_renewed = PackageInvoiceService.expire_prepaid(
            subscription_code,
        )
        subscription_object = CommonService.get_subscription_object(
            customer_code=None,
            subscription_code=subscription_code,
        )
        number = subscription_object.number
        customer_code = subscription_object.customer.customer_code
        notify_object = {
            "customer_code": customer_code,
            "subscription_code": subscription_code,
            "number": number,
        }
        tb_notify_type = TB_NOTIFY.PREPAID_EXPIRED
        if is_renewed:
            tb_notify_type = TB_NOTIFY.PREPAID_RENEWED
        try:
            TrunkService.notify_trunk_backend(
                notify_type_code=tb_notify_type,
                notify_object=notify_object,
            )
        except api_exceptions.APIException as e:
            JobService.add_failed_job(
                FinanceConfigurations.Jobs.TYPES[1][0],
                'v1',
                'TrunkService',
                'notify_trunk_backend',
                json.dumps({
                    "notify_type_code": tb_notify_type,
                    "notify_object": notify_object,
                }),
                str(e),
            )
