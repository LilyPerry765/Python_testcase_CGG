# --------------------------------------------------------------------------
# Handle logics related to Invoice objects.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - invoice.py
# Created at 2020-8-29,  17:21:36
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import math
import uuid
from datetime import (
    datetime,
    timedelta,
)
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
)

import pytz
from celery import shared_task
from django.conf import settings
from django.db import DataError, transaction
from django.utils.translation import gettext as _
from jdatetime import datetime as jdatetime

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import (
    Invoice,
    PackageInvoice, Subscription,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.invoice import (
    ExportInvoiceSerializer,
    InvoiceSerializer,
)
from cgg.apps.finance.versions.v1.services.branch import BranchService
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.credit_invoice import (
    CreditInvoiceService,
)
from cgg.apps.finance.versions.v1.services.destination import (
    DestinationService,
)
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.mis import MisService
from cgg.apps.finance.versions.v1.services.runtime_config import (
    RuntimeConfigService,
)
from cgg.apps.finance.versions.v1.services.tax import TaxService
from cgg.apps.finance.versions.v1.services.trunk import TrunkService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools

invoice_config = FinanceConfigurations.Invoice


@shared_task
def continue_issuing_interim_invoice(
        customer_code,
        subscription_code,
        from_date,
        description,
        bypass_type,
        on_demand,
):
    """
    Handle issuing interim invoices non blocking
    :param customer_code:
    :param subscription_code:
    :param from_date:
    :param description:
    :param bypass_type:
    :param on_demand:
    :return:
    """
    subscription_object = CommonService.get_subscription_object(
        customer_code=customer_code,
        subscription_code=subscription_code,
    )
    from_date = datetime.fromtimestamp(from_date)
    to_date = datetime.now()
    invoice_object, payed = InvoiceService.issue_invoice(
        subscription_object,
        from_date,
        to_date,
        invoice_config.TYPES[1][0],
        description,
        on_demand=on_demand,
    )
    subscription_object.interim_processed()
    if invoice_object:
        if bypass_type == invoice_config.BypassType.DEALLOCATE:
            invoice_cause = _("Deallocation of subscription")
        elif bypass_type == invoice_config.BypassType.EIGHTY_PERCENT:
            invoice_cause = _("Eighty percent usage")
        elif bypass_type == invoice_config.BypassType.MAX_USAGE:
            invoice_cause = _("Max usage")
        else:
            invoice_cause = _("Your request") if on_demand else _(
                "Nexfon support request"
            )
        notify_object = {
            "customer_code": str(invoice_object['customer_code']),
            "subscription_code": str(invoice_object['subscription_code']),
            "number": str(invoice_object['number']),
            "invoice_id": str(invoice_object['id']),
            "total_cost": str(invoice_object['total_cost']),
            "cause": invoice_cause,
        }
        tb_notify_type = \
            FinanceConfigurations.TrunkBackend.Notify.INTERIM_INVOICE
        if payed:
            tb_notify_type = \
                FinanceConfigurations.TrunkBackend.Notify \
                    .INTERIM_INVOICE_AUTO_PAYED
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
                str(e)
            )

    return True


@shared_task
def restart_issuing_interim_invoice(
        customer_code,
        subscription_code,
        description,
        bypass_type,
        on_demand,
):
    """
    Handle issuing interim invoices with delay in case on payment cool down
    for anything other than no bypass mode
    :param customer_code:
    :param subscription_code:
    :param description:
    :param bypass_type:
    :param on_demand:
    :return:
    """
    try:
        latest_invoice = Invoice.objects.filter(
            subscription__subscription_code=subscription_code,
        ).latest('created_at')
    except Invoice.DoesNotExist:
        latest_invoice = None

    if latest_invoice is None or (
            latest_invoice and latest_invoice.status_code !=
            invoice_config.STATE_CHOICES[2][0]
    ):
        InvoiceService.issue_interim_invoice(
            customer_code,
            subscription_code,
            description,
            bypass_type,
            on_demand,
        )


class InvoiceService:

    @classmethod
    def get_invoice(
            cls,
            customer_code,
            subscription_code,
            invoice_id,
    ):
        """
        Get details of an invoice
        :param customer_code:
        :param subscription_code:
        :param invoice_id:
        :return:
        """
        Tools.uuid_validation(invoice_id)
        other_conditions = CommonService.base_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            query_invoice = Invoice.objects.get(
                id=invoice_id,
                **other_conditions,
            )
        except Invoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.INVOICE_404,
            )

        invoice_serializer = InvoiceSerializer(query_invoice)

        return invoice_serializer.data

    @classmethod
    def get_invoices(
            cls,
            customer_code,
            subscription_code,
            request,
            export_type=FinanceConfigurations.Export.Format.JSON,
    ):
        """
        Get all invoices based on subscription, customer and query params
        :param export_type:
        :type export_type:
        :param customer_code:
        :param subscription_code:
        :param request:
        :return:
        """
        query_params = request.query_params
        other_conditions = CommonService.base_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        query_invoice = Invoice.objects.filter(
            **other_conditions,
        )

        if query_params is not None:
            query_invoice = CommonService.filter_and_order_base_invoice(
                Invoice,
                query_invoice,
                query_params,
            )

        if FinanceConfigurations.Export.Format.is_json(export_type):
            query_invoice, paginator = Paginator().paginate(
                request=request,
                queryset=query_invoice,
            )
            invoice_serializer = InvoiceSerializer(
                query_invoice,
                many=True,
            )
            data = invoice_serializer.data, paginator
        else:
            invoice_serializer = ExportInvoiceSerializer(
                query_invoice,
                many=True,
            )
            data = invoice_serializer.data

        return data

    @classmethod
    def calculate_total_cost(
            cls,
            landlines_local_cost,
            landlines_long_distance_cost,
            landlines_corporate_cost,
            mobile_cost,
            international_cost,
            tax_cost,
            subscription_fee,
            debt,
            discount,
    ):
        """
        Calculate the total cost of an invoice base on all costs, debt and
        discounts and return it
        :param landlines_local_cost:
        :param landlines_long_distance_cost:
        :param landlines_corporate_cost:
        :param mobile_cost:
        :param international_cost:
        :param tax_cost:
        :param subscription_fee:
        :param debt:
        :param discount:
        :return: Decimal of total cost
        """
        total_cost = Decimal(landlines_local_cost) + Decimal(
            landlines_long_distance_cost) + Decimal(
            landlines_corporate_cost) + Decimal(mobile_cost) + Decimal(
            international_cost) + Decimal(tax_cost) + Decimal(
            subscription_fee) + Decimal(debt) - Decimal(discount)

        if Decimal(total_cost) < 0:
            return Decimal(0)

        return total_cost

    @classmethod
    def calculate_tax(
            cls,
            landlines_local_cost,
            landlines_long_distance_cost,
            landlines_corporate_cost,
            mobile_cost,
            international_cost,
            subscription_fee,
            tax_percent,
    ):
        """
        Calculate tax cost based on RuntimeConfig tax percent
        :param landlines_local_cost:
        :param landlines_long_distance_cost:
        :param landlines_corporate_cost:
        :param mobile_cost:
        :param international_cost:
        :param subscription_fee:
        :param tax_percent:
        :return: Decimal : tax_cost
        """
        total_pure_cost = Decimal(landlines_local_cost) + Decimal(
            landlines_long_distance_cost) + Decimal(mobile_cost) + Decimal(
            subscription_fee) + Decimal(international_cost) + Decimal(
            landlines_corporate_cost)
        tax_cost = (total_pure_cost * Decimal(tax_percent)) / Decimal(100)

        return Decimal(tax_cost).to_integral_exact(rounding=ROUND_CEILING)

    @classmethod
    def calculate_usages_minimal(
            cls,
            subscription_code,
            from_date,
    ):
        cdrs = BasicService.get_cdrs(
            subscription_codes=[subscription_code],
            created_at_start=str(from_date.timestamp()).split('.')[0] if
            from_date else "",
        )
        cdrs = BasicService.cdrs_minimal_object(
            cdrs,
        )
        used_cdrs = []
        cost_postpaid = Decimal(0)
        cost_prepaid = Decimal(0)
        for cdr in cdrs:
            if cdr['cgr_id'] not in used_cdrs:
                if cdr["extra_fields"]["balance_type"] == \
                        FinanceConfigurations.Subscription.TYPE[0][0]:
                    cost_postpaid += Decimal(cdr['cost'])
                else:
                    cost_prepaid += Decimal(cdr['cost'])

                used_cdrs.append(cdr['cgr_id'])

        return {
            "cost_postpaid": cost_postpaid,
            "cost_prepaid": cost_prepaid,
        }

    @classmethod
    def calculate_usages(
            cls,
            subscription_code,
            from_date,
            to_date,
    ):
        """
        Calculate usages and costs based on CDRs
        :param subscription_code:
        :param from_date:
        :param to_date:
        :return:
        """
        prefixes_landline_local = \
            DestinationService.get_prefixes_landline_local(
                subscription_code,
            )
        prefixes_landline_long_distance = \
            DestinationService.get_prefixes_landline_long_distance(
                subscription_code,
            )
        prefixes_landline_corporate = \
            DestinationService.get_prefixes_landline_corporate()
        prefixes_landline_branches = \
            BranchService.get_not_default_destinations()
        prefixes_mobile = DestinationService.get_prefixes_mobile()
        prefixes_international = \
            DestinationService.get_prefixes_international()

        # landlines_local_object = BasicService.get_cdrs(
        #     subscription_codes=[subscription_code],
        #     created_at_start=str(from_date.timestamp()).split('.')[0],
        #     created_at_end=str(to_date.timestamp()).split('.')[0],
        #     destination_prefixes=prefixes_landline_local,
        #     not_destination_prefixes=list(
        #         prefixes_international + prefixes_mobile +
        #         prefixes_landline_corporate + prefixes_landline_long_distance
        #     ),
        # )

        landlines_local_object_count = BasicService.get_cdrs_count(
            subscription_codes=[subscription_code],
            created_at_start=str(from_date.timestamp()).split('.')[0],
            created_at_end=str(to_date.timestamp()).split('.')[0],
            destination_prefixes=prefixes_landline_local,
            not_destination_prefixes=list(
                prefixes_international + prefixes_mobile +
                prefixes_landline_corporate + prefixes_landline_long_distance
            ),
        )

        with open('logs.txt', 'w') as f:
            f.write('\n landlines_local_object_count : ' + str(landlines_local_object_count))


        # landlines_long_distance_object = BasicService.get_cdrs(
        #     subscription_codes=[subscription_code],
        #     created_at_start=str(from_date.timestamp()).split('.')[0],
        #     created_at_end=str(to_date.timestamp()).split('.')[0],
        #     destination_prefixes=prefixes_landline_long_distance,
        #     not_destination_prefixes=list(
        #         prefixes_international + prefixes_mobile +
        #         prefixes_landline_corporate + prefixes_landline_local
        #     ),
        # )

        landlines_long_distance_object_count = BasicService.get_cdrs_count(
            subscription_codes=[subscription_code],
            created_at_start=str(from_date.timestamp()).split('.')[0],
            created_at_end=str(to_date.timestamp()).split('.')[0],
            destination_prefixes=prefixes_landline_long_distance,
            not_destination_prefixes=list(
                prefixes_international + prefixes_mobile +
                prefixes_landline_corporate + prefixes_landline_local
            ),
        )

        with open('logs.txt', 'a') as f:
            f.write('\n landlines_long_distance_object_count: ' + str(landlines_long_distance_object_count))




        # landlines_corporate_object = BasicService.get_cdrs(
        #     subscription_codes=[subscription_code],
        #     created_at_start=str(from_date.timestamp()).split('.')[0],
        #     created_at_end=str(to_date.timestamp()).split('.')[0],
        #     destination_prefixes=prefixes_landline_corporate,
        #     not_destination_prefixes=[
        #         d for d in list(
        #             prefixes_international + prefixes_mobile +
        #             prefixes_landline_local + prefixes_landline_long_distance
        #         ) if d not in prefixes_landline_branches
        #     ],
        # )


        landlines_corporate_object_count = BasicService.get_cdrs_count(
            subscription_codes=[subscription_code],
            created_at_start=str(from_date.timestamp()).split('.')[0],
            created_at_end=str(to_date.timestamp()).split('.')[0],
            destination_prefixes=prefixes_landline_corporate,
            not_destination_prefixes=[
                d for d in list(
                    prefixes_international + prefixes_mobile +
                    prefixes_landline_local + prefixes_landline_long_distance
                ) if d not in prefixes_landline_branches
            ],
        )

        with open('logs.txt', 'a') as f:
            f.write('\n landlines_corporate_object_count: ' + str(landlines_corporate_object_count))


        # mobiles_national_object = BasicService.get_cdrs(
        #     subscription_codes=[subscription_code],
        #     created_at_start=str(from_date.timestamp()).split('.')[0],
        #     created_at_end=str(to_date.timestamp()).split('.')[0],
        #     destination_prefixes=prefixes_mobile,
        #     not_destination_prefixes=list(
        #         prefixes_international + prefixes_landline_corporate +
        #         prefixes_landline_local + prefixes_landline_long_distance
        #     ),
        # )


        mobiles_national_object_count = BasicService.get_cdrs(
            subscription_codes=[subscription_code],
            created_at_start=str(from_date.timestamp()).split('.')[0],
            created_at_end=str(to_date.timestamp()).split('.')[0],
            destination_prefixes=prefixes_mobile,
            not_destination_prefixes=list(
                prefixes_international + prefixes_landline_corporate +
                prefixes_landline_local + prefixes_landline_long_distance
            ),
        )

        with open('logs.txt', 'a') as f:
            f.write('\n mobiles_national_object_count: ' + str(mobiles_national_object_count))



        # international_object = BasicService.get_cdrs(
        #     subscription_codes=[subscription_code],
        #     created_at_start=str(from_date.timestamp()).split('.')[0],
        #     created_at_end=str(to_date.timestamp()).split('.')[0],
        #     destination_prefixes=prefixes_international,
        #     not_destination_prefixes=list(
        #         prefixes_mobile + prefixes_landline_corporate +
        #         prefixes_landline_local + prefixes_landline_long_distance
        #     ),
        # )


        international_object_count = BasicService.get_cdrs_count(
            subscription_codes=[subscription_code],
            created_at_start=str(from_date.timestamp()).split('.')[0],
            created_at_end=str(to_date.timestamp()).split('.')[0],
            destination_prefixes=prefixes_international,
            not_destination_prefixes=list(
                prefixes_mobile + prefixes_landline_corporate +
                prefixes_landline_local + prefixes_landline_long_distance
            ),
        )

        with open('logs.txt', 'a') as f:
            f.write('\n international_object_count: ' + str(international_object_count))



        all_sub_c_cdrs_count = BasicService.get_cdrs_count(
            subscription_codes=[subscription_code],
        )

        with open('logs.txt', 'a') as f:
            f.write('\n all_sub_c_cdrs_count: ' + str(all_sub_c_cdrs_count))


        





        landlines_local_list = BasicService.cdrs_minimal_object(
            landlines_local_object,
        )
        landlines_long_distance_list = BasicService.cdrs_minimal_object(
            landlines_long_distance_object,
        )
        mobiles_list = BasicService.cdrs_minimal_object(
            mobiles_national_object,
        )
        internationals_list = BasicService.cdrs_minimal_object(
            international_object,
        )
        landlines_corporate_list = BasicService.cdrs_minimal_object(
            landlines_corporate_object,
        )
        mobile_usage = Decimal(0)
        mobile_cost = Decimal(0)
        landline_local_usage = Decimal(0)
        landline_local_cost = Decimal(0)
        landline_long_distance_usage = Decimal(0)
        landline_long_distance_cost = Decimal(0)
        landlines_corporate_usage = Decimal(0)
        landlines_corporate_cost = Decimal(0)
        international_usage = Decimal(0)
        international_cost = Decimal(0)
        mobile_usage_prepaid = Decimal(0)
        mobile_cost_prepaid = Decimal(0)
        landline_local_usage_prepaid = Decimal(0)
        landline_local_cost_prepaid = Decimal(0)
        landline_long_distance_usage_prepaid = Decimal(0)
        landline_long_distance_cost_prepaid = Decimal(0)
        landlines_corporate_usage_prepaid = Decimal(0)
        landlines_corporate_cost_prepaid = Decimal(0)
        international_usage_prepaid = Decimal(0)
        international_cost_prepaid = Decimal(0)
        used_cdrs = []

        for landlines_item in landlines_corporate_list:
            if landlines_item['cgr_id'] not in used_cdrs:
                if landlines_item["extra_fields"]["balance_type"] == \
                        FinanceConfigurations.Subscription.TYPE[0][0]:
                    landlines_corporate_usage += Decimal(
                        landlines_item['usage'])
                    landlines_corporate_cost += Decimal(landlines_item['cost'])
                else:
                    landlines_corporate_usage_prepaid += Decimal(
                        landlines_item['usage'],
                    )
                    landlines_corporate_cost_prepaid += Decimal(
                        landlines_item['cost'],
                    )

                used_cdrs.append(landlines_item['cgr_id'])

        for landlines_item in landlines_local_list:
            if landlines_item['cgr_id'] not in used_cdrs:
                if landlines_item["extra_fields"]["balance_type"] == \
                        FinanceConfigurations.Subscription.TYPE[0][0]:
                    if landlines_item['category'] == 'BR_Tehran':
                        landline_local_usage += cls.round_to_nearest_min(Decimal(landlines_item['usage']))
                    else:
                        landline_local_usage += cls.round_to_nearest_half_min(Decimal(landlines_item['usage']))
                    landline_local_cost += Decimal(landlines_item['cost'])
                else:
                    if landlines_item['category'] == 'BR_Tehran':
                        landline_local_usage_prepaid += cls.round_to_nearest_min(Decimal(
                            landlines_item['usage'],
                        ))
                    else:
                        landline_local_usage_prepaid += cls.round_to_nearest_half_min(Decimal(
                            landlines_item['usage'],
                        ))

                    landline_local_cost_prepaid += Decimal(
                        landlines_item['cost'],
                    )

                used_cdrs.append(landlines_item['cgr_id'])

        for landlines_item in landlines_long_distance_list:
            if landlines_item['cgr_id'] not in used_cdrs:
                if landlines_item["extra_fields"]["balance_type"] == \
                        FinanceConfigurations.Subscription.TYPE[0][0]:
                    landline_long_distance_usage += cls.round_to_nearest_half_min(Decimal(
                        landlines_item['usage'],
                    ))
                    landline_long_distance_cost += Decimal(
                        landlines_item['cost'],
                    )
                else:
                    landline_long_distance_usage_prepaid += cls.round_to_nearest_half_min(Decimal(
                        landlines_item['usage'],
                    ))
                    landline_long_distance_cost_prepaid += Decimal(
                        landlines_item['cost'],
                    )
                used_cdrs.append(landlines_item['cgr_id'])

        for mobiles_item in mobiles_list:
            if mobiles_item['cgr_id'] not in used_cdrs:
                if mobiles_item["extra_fields"]["balance_type"] == \
                        FinanceConfigurations.Subscription.TYPE[0][0]:
                    mobile_usage += cls.round_to_nearest_half_min(Decimal(mobiles_item['usage']))
                    mobile_cost += Decimal(mobiles_item['cost'])
                else:
                    mobile_usage_prepaid += cls.round_to_nearest_half_min(Decimal(mobiles_item['usage']))
                    mobile_cost_prepaid += Decimal(mobiles_item['cost'])
                used_cdrs.append(mobiles_item['cgr_id'])

        for internationals_item in internationals_list:
            if internationals_item['cgr_id'] not in used_cdrs:
                if internationals_item["extra_fields"]["balance_type"] == \
                        FinanceConfigurations.Subscription.TYPE[0][0]:
                    international_usage += Decimal(
                        internationals_item['usage'],
                    )
                    international_cost += Decimal(internationals_item['cost'])
                else:
                    international_usage_prepaid += Decimal(
                        internationals_item['usage'],
                    )
                    international_cost_prepaid += Decimal(
                        internationals_item['cost'],
                    )

                used_cdrs.append(internationals_item['cgr_id'])

        cost_usage_dict = {
            # Postpaid part of usages and costs
            'landlines_corporate_usage': Decimal(
                landlines_corporate_usage,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_corporate_cost': Decimal(
                landlines_corporate_cost,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_local_cost': Decimal(
                landline_local_cost,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_local_usage': Decimal(
                landline_local_usage,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_long_distance_cost': Decimal(
                landline_long_distance_cost,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_long_distance_usage': Decimal(
                landline_long_distance_usage,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'mobile_cost': Decimal(mobile_cost).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            'mobile_usage': Decimal(mobile_usage).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            'international_cost': Decimal(
                international_cost).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            'international_usage': Decimal(
                international_usage).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            # Prepaid part of usages and costs
            'landlines_corporate_usage_prepaid': Decimal(
                landlines_corporate_usage_prepaid,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_corporate_cost_prepaid': Decimal(
                landlines_corporate_cost_prepaid,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_local_cost_prepaid': Decimal(
                landline_local_cost_prepaid,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_local_usage_prepaid': Decimal(
                landline_local_usage_prepaid,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_long_distance_cost_prepaid': Decimal(
                landline_long_distance_cost_prepaid,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'landlines_long_distance_usage_prepaid': Decimal(
                landline_long_distance_usage_prepaid,
            ).to_integral_exact(rounding=ROUND_CEILING),
            'mobile_cost_prepaid': Decimal(
                mobile_cost_prepaid).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            'mobile_usage_prepaid': Decimal(
                mobile_usage_prepaid).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            'international_cost_prepaid': Decimal(
                international_cost_prepaid).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
            'international_usage_prepaid': Decimal(
                international_usage_prepaid).to_integral_exact(
                rounding=ROUND_CEILING,
            ),
        }

        return cost_usage_dict

    @classmethod
    def round_to_nearest_half_min(cls, time):
        return Decimal(time / 30000000000).to_integral_exact(rounding=ROUND_CEILING) * 30000000000

    @classmethod
    def round_to_nearest_min(cls, time):
        return Decimal(time / 60000000000).to_integral_exact(rounding=ROUND_CEILING) * 60000000000

    @classmethod
    def calculate_discount(
            cls,
            landlines_local_cost,
            landlines_long_distance_cost,
            landlines_corporate_cost,
            mobile_cost,
            international_cost,
            tax_cost,
            subscription_fee,
            debt
    ):
        """
        Calculate discount on total cost
        :param landlines_corporate_cost:
        :param landlines_local_cost:
        :param landlines_long_distance_cost:
        :param mobile_cost:
        :param international_cost:
        :param tax_cost:
        :param subscription_fee:
        :param debt:
        :return: a dict that contains discount and discount_description
        """
        total_cost = Decimal(landlines_local_cost) + Decimal(
            landlines_long_distance_cost) + Decimal(mobile_cost) + Decimal(
            international_cost) + Decimal(tax_cost) + Decimal(
            subscription_fee) + Decimal(debt) + Decimal(
            landlines_corporate_cost)
        global_discount_value = cls.get_discount_value(
            discount_type=0,
        )
        global_discount_percent = cls.get_discount_value(
            discount_type=1,
        )
        discount_percent = (Decimal(total_cost) * Decimal(
            global_discount_percent
        )) / Decimal(100)
        discount = discount_percent + Decimal(global_discount_value)

        if Decimal(discount) < Decimal(0):
            discount = Decimal(0)

        if Decimal(discount) > Decimal(total_cost):
            discount = total_cost

        message_rial = _("Rial")
        message_subtract_discount = _(
            'subtracted for this invoice',
        )

        discount_description = ""

        if discount > Decimal(0):
            discount_description = f"{discount} {message_rial} " \
                                   f"{message_subtract_discount}."

        data = {
            'discount_description': discount_description,
            'discount':
                Decimal(discount).to_integral_exact(rounding=ROUND_CEILING)
        }

        return data

    @classmethod
    def get_due_date(cls, invoice_type_code):
        """
        Get due date of an invoice based on RuntimeConfig settings
        :param: invoice_type_code
        :return:
        """
        if invoice_type_code == invoice_config.TYPES[1][0]:
            return None

        due_date = int(RuntimeConfigService.get_value(
            FinanceConfigurations.RuntimeConfig.KEY_CHOICES[1][0],
        ))
        today_jalali = jdatetime.now(tz=pytz.timezone("Asia/Tehran"))
        month = today_jalali.month
        year = today_jalali.year
        month += due_date

        if month > 12:
            year += 1
            month -= 12

        due_date_jalali = jdatetime(
            year=year,
            month=month,
            day=today_jalali.day,
            hour=today_jalali.hour,
            minute=today_jalali.minute,
            second=today_jalali.second,
            microsecond=today_jalali.microsecond,
        )

        return due_date_jalali.togregorian()

    @classmethod
    def can_issue_new_interim(cls, latest_invoice, on_demand=False):
        """
        Check whether it's possible to issue a new interim invoice
        :param on_demand:
        :type on_demand:
        :param latest_invoice:
        :return:
        """
        new_invoice_hours = int(RuntimeConfigService.get_value(
            FinanceConfigurations.RuntimeConfig.KEY_CHOICES[0][0],
        ))
        if latest_invoice.on_demand and on_demand and \
                latest_invoice.status_code not in (
                invoice_config.STATE_CHOICES[2][0],
                invoice_config.STATE_CHOICES[3][0],
        ):
            raise api_exceptions.Conflict409(
                _(
                    'Previous requested invoice is already active, can not '
                    'request another interim invoice for now!'
                ),
            )
        if latest_invoice.created_at >= datetime.now() - timedelta(
                hours=new_invoice_hours
        ):
            raise api_exceptions.Conflict409(
                _('Can not issue another interim invoice for now!'),
            )

    @classmethod
    def issue_invoice(
            cls,
            subscription_object,
            from_date,
            to_date,
            invoice_type_code,
            description,
            on_demand=False,
    ):
        """
        Base method to create a new invoice that could be periodic to interim
        :param on_demand: check whether invoice created by demand or
        automatically
        :param description: string
        :param subscription_object: an object from Subscription
        :param from_date: datetime
        :param to_date: datetime
        :param invoice_type_code: periodic or interim from configs
        :return:
        """
        invoice_dict = dict()
        with transaction.atomic():
            try:
                latest_invoice = Invoice.objects.filter(
                    subscription=subscription_object
                ).select_for_update().latest(
                    'created_at',
                )
            except Invoice.DoesNotExist:
                latest_invoice = None

            if latest_invoice is not None:
                invoice_dict['period_count'] = int(
                    latest_invoice.period_count
                ) + 1
                if latest_invoice.status_code != \
                        invoice_config.STATE_CHOICES[2][0]:
                    latest_invoice.status_code = \
                        invoice_config.STATE_CHOICES[3][0]
                    latest_invoice.updated_status_at = datetime.now()
                    latest_invoice.save()
                    invoice_dict['debt'] = Decimal(
                        latest_invoice.total_cost
                    ).to_integral_exact(rounding=ROUND_CEILING)
                else:
                    invoice_dict['debt'] = Decimal(latest_invoice.difference_with_rounded)
            else:
                invoice_dict['period_count'] = int(1)
                invoice_dict['debt'] = Decimal(0)

        invoice_dict['subscription'] = subscription_object
        invoice_dict['invoice_type_code'] = invoice_type_code
        invoice_dict['from_date'] = from_date
        invoice_dict['to_date'] = to_date
        invoice_dict['updated_status_at'] = datetime.now()
        invoice_dict['tracking_code'] = uuid.uuid4()
        invoice_dict['status_code'] = invoice_config.STATE_CHOICES[0][0]
        usage_info = cls.calculate_usages(
            subscription_object.subscription_code,
            invoice_dict['from_date'],
            invoice_dict['to_date'],
        )
        invoice_dict.update(
            usage_info,
        )
        invoice_dict['subscription_fee'] = MisService.get_subscription_fee(
            invoice_type_code,
            subscription_object.subscription_code,
            to_date,
        )
        invoice_dict['due_date'] = cls.get_due_date(
            invoice_dict['invoice_type_code'],
        )
        invoice_dict['description'] = description
        invoice_dict['tax_percent'] = TaxService.get_tax_percent()
        invoice_dict['tax_cost'] = cls.calculate_tax(
            invoice_dict['landlines_local_cost'],
            invoice_dict['landlines_long_distance_cost'],
            invoice_dict['landlines_corporate_cost'],
            invoice_dict['mobile_cost'],
            invoice_dict['international_cost'],
            invoice_dict['subscription_fee'],
            invoice_dict['tax_percent'],
        )
        discount_details = cls.calculate_discount(
            invoice_dict['landlines_local_cost'],
            invoice_dict['landlines_long_distance_cost'],
            invoice_dict['landlines_corporate_cost'],
            invoice_dict['mobile_cost'],
            invoice_dict['international_cost'],
            invoice_dict['tax_cost'],
            invoice_dict['subscription_fee'],
            invoice_dict['debt']
        )
        invoice_dict['discount'] = discount_details['discount']
        invoice_dict['discount_description'] = \
            discount_details['discount_description']
        invoice_dict['total_cost'] = cls.calculate_total_cost(
            invoice_dict['landlines_local_cost'],
            invoice_dict['landlines_long_distance_cost'],
            invoice_dict['landlines_corporate_cost'],
            invoice_dict['mobile_cost'],
            invoice_dict['international_cost'],
            invoice_dict['tax_cost'],
            invoice_dict['subscription_fee'],
            invoice_dict['debt'],
            invoice_dict['discount'],
        )
        invoice_dict['on_demand'] = on_demand
        try:
            invoice_object = Invoice(**invoice_dict)
            invoice_object.save()
            invoice_object, pay_notify = cls.handle_auto_pay_and_zero_invoice(
                invoice_object,
            )
            invoice_serializer = InvoiceSerializer(invoice_object)
            response_data = invoice_serializer.data
        except (InvalidOperation, DataError):
            raise api_exceptions.APIException(
                _('Invalid operation in Decimal or Integer fields')
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)

        return response_data, pay_notify

    @classmethod
    def issue_interim_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            description='',
            bypass_type=
            invoice_config.BypassType.NO_BYPASS,
            on_demand=False,
    ):
        """
        Issue an interim invoice for limited subscriptions
        :param on_demand:
        :param customer_code:
        :param subscription_code:
        :param description:
        :param bypass_type:
        :return:
        """
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )

        print('my subscription_object')
        print(subscription_object)
        if subscription_object.subscription_type == \
                FinanceConfigurations.Subscription.TYPE[2][0]:
            raise api_exceptions.Conflict409(
                ErrorMessages.SUBSCRIPTION_409_UNLIMITED
            )
        if subscription_object.subscription_type == \
                FinanceConfigurations.Subscription.TYPE[1][0]:
            raise api_exceptions.Conflict409(
                ErrorMessages.SUBSCRIPTION_409_PREPAID
            )

        if bypass_type == invoice_config.BypassType.NO_BYPASS and \
                subscription_object.interim_request:
            raise api_exceptions.Conflict409(
                _(
                    'Previous requested invoice is not processed yet, '
                    'please try again in a while'
                ),
            )

        try:
            latest_invoice = Invoice.objects.filter(
                subscription=subscription_object,
            ).latest('created_at')
            from_date = latest_invoice.to_date + timedelta(microseconds=1)
        except Invoice.DoesNotExist:
            latest_invoice = None
            from_date = subscription_object.created_at + timedelta(
                microseconds=1
            )
        if latest_invoice:
            if bypass_type == invoice_config.BypassType.NO_BYPASS:
                cls.can_issue_new_interim(latest_invoice, on_demand)
                if latest_invoice.pay_cool_down \
                        and latest_invoice.pay_cool_down > datetime.now():
                    raise api_exceptions.Conflict409(
                        ErrorMessages.PAYMENT_409_COOL_DOWN_PREVIOUS,
                    )
            else:
                should_restart = False
                check_time = datetime.now() + timedelta(
                    seconds=15,
                )

                if latest_invoice.pay_cool_down \
                        and latest_invoice.pay_cool_down > datetime.now():
                    check_time = latest_invoice.pay_cool_down + timedelta(
                        milliseconds=1,
                    )
                    should_restart = True

                if subscription_object.interim_request:
                    should_restart = True

                if should_restart:
                    restart_issuing_interim_invoice.apply_async(
                        args=(
                            customer_code,
                            subscription_code,
                            description,
                            bypass_type,
                            on_demand,
                        ),
                        eta=check_time,
                    )
                    return

        subscription_object.interim_requested()
        continue_issuing_interim_invoice.apply_async(
            args=(
                customer_code,
                subscription_code,
                from_date.timestamp(),
                description,
                bypass_type,
                on_demand,
            ),
        )

        with(open('khosro_logs.txt', 'a')) as f:
            f.write('issue_interim_invoice done')
            f.write('\n')
        return True

    @classmethod
    def issue_periodic_invoice(
            cls,
            subscription_id,
            from_date,
            to_date,
            description='',
            notify_singular=False,
    ):
        """
        This method is related to Jobs
        :param notify_singular: notify trunk backend if necessary
        :param description: string
        :param subscription_id: an object from subscription model
        :param from_date: start of period (string or datetime object)
        :param to_date: end of period (string or datetime object)
        :return a new invoice
        """
        invoice_type_code = invoice_config.TYPES[0][0]
        invoice_object = None

        if isinstance(from_date, str):
            from_date = datetime.fromtimestamp(float(from_date))

        if isinstance(to_date, str):
            to_date = datetime.fromtimestamp(float(to_date))

        # Check latest invoice and subscription's created at. Change
        # from date if necessary
        try:
            subscription_object = Subscription.objects.get(
                id=subscription_id,
                is_allocated=True,
            )
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.SUBSCRIPTION_404,
            )

        if subscription_object.subscription_type == \
                FinanceConfigurations.Subscription.TYPE[2][0]:
            raise api_exceptions.Conflict409(
                ErrorMessages.SUBSCRIPTION_409_UNLIMITED
            )

        if from_date < subscription_object.created_at:
            from_date = subscription_object.created_at + timedelta(
                microseconds=1,
            )

        should_issue = True
        try:
            latest_invoice = Invoice.objects.filter(
                subscription=subscription_object,
            ).latest(
                'created_at',
            )
            if to_date == latest_invoice.to_date:
                # this is it, no need to create a new one
                should_issue = False
            if from_date < latest_invoice.to_date:
                from_date = latest_invoice.to_date
        except Invoice.DoesNotExist:
            pass

        payed = False
        if should_issue:
            invoice_object, payed = cls.issue_invoice(
                subscription_object,
                from_date,
                to_date,
                invoice_type_code,
                description,
            )

            if invoice_object is not None and notify_singular:
                notify_object = [{
                    "customer_code":
                        str(invoice_object['customer_code']),
                    "subscription_code": str(
                        invoice_object['subscription_code']
                    ),
                    "number": str(
                        invoice_object['number']
                    ),
                    'invoice_id': str(invoice_object['id']),
                    'total_cost': str(invoice_object['total_cost']),
                    'auto_payed': payed,
                }]
                try:
                    TrunkService.notify_trunk_backend(
                        notify_type_code=FinanceConfigurations.TrunkBackend
                            .Notify.PERIODIC_INVOICE,
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
                                FinanceConfigurations.TrunkBackend
                                    .Notify.PERIODIC_INVOICE,
                            "notify_object": notify_object,
                        }),
                        str(e)
                    )

        return invoice_object, payed

    @classmethod
    def get_discount_value(cls, discount_type):
        """
        Get discount value based on RuntimeConfig and discount type. Two
        types of discount are available (Percent and Concrete)
        :param discount_type:
        :return:
        """
        if discount_type == 0:
            item_key = FinanceConfigurations.RuntimeConfig.KEY_CHOICES[4][0]
        else:
            item_key = FinanceConfigurations.RuntimeConfig.KEY_CHOICES[5][0]

        return RuntimeConfigService.get_value(item_key)

    @classmethod
    def handle_auto_pay_and_zero_invoice(cls, invoice_object):
        should_issue = False
        description = None
        if Decimal(invoice_object.total_cost) == Decimal(0):
            description = _(
                "This credit invoice is generated automatically to "
                "pay for an invoice with zero total cost",
            )
            should_issue = True
        elif Decimal(invoice_object.total_cost) > Decimal(0) and Decimal(
                invoice_object.subscription.customer.credit) >= Decimal(
            invoice_object.total_cost) and \
                invoice_object.subscription.auto_pay:
            description = _(
                "This credit invoice is generated automatically to "
                "pay for an invoice in auto pay mode",
            )
            should_issue = True
        if should_issue:
            try:
                CreditInvoiceService.decrease_credit(
                    customer_object=invoice_object.subscription.customer,
                    used_for=FinanceConfigurations.CreditInvoice.USED_FOR[0][
                        0],
                    used_for_id=invoice_object.id,
                    description=description
                )
                invoice_object = Invoice.objects.get(
                    id=invoice_object.id,
                )
            except api_exceptions.APIException:
                pass

        return invoice_object, should_issue

    @classmethod
    def delete_invoice(cls, invoice_id):
        try:
            delete_invoice = Invoice.objects.get(
                id=invoice_id,
            )
        except Invoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.INVOICE_404,
            )
        if delete_invoice.status_code in (
                invoice_config.STATE_CHOICES[2][0],
                invoice_config.STATE_CHOICES[3][0],
        ):
            raise api_exceptions.Conflict409(
                _("Can not delete this invoice with this status code")
            )
        subscription = delete_invoice.subscription
        delete_invoice.delete()

        with transaction.atomic():
            try:
                latest_invoice = Invoice.objects.filter(
                    subscription=subscription,
                ).select_for_update().latest('created_at')
            except Invoice.DoesNotExist:
                return

            if latest_invoice.status_code == \
                    invoice_config.STATE_CHOICES[3][0]:
                latest_invoice.status_code = invoice_config.STATE_CHOICES[0][0]
                latest_invoice.save()

    @classmethod
    def verify_and_repair(
            cls,
            branch_code,
            subscription_code,
            max_usage=False,
            is_prepaid=False,
    ):
        """
        Verify the correctness of 80 and 100 percent events and fix sessions
        :param max_usage:
        :param branch_code:
        :param subscription_code:
        :param is_prepaid:
        :return:
        """
        # Phase 1: Go through active sessions unconditionally
        BasicService.disconnect_sessions(
            subscription_code=subscription_code,
            setup_time=datetime.now() - timedelta(
                seconds=int(settings.CGG['MAX_CALL_DURATION'])
            )
        )
        # Phase 2: Repair the current balance if needed
        total_active = cls._total_unpaid_active(subscription_code)
        total_unpaid = cls._total_unpaid_usages(
            subscription_code,
            is_prepaid,
        )
        total_cost = total_active + total_unpaid
        balances = BasicService.get_balance(subscription_code, True)
        if max_usage:
            check_value = Decimal(
                BasicService.get_branch_maximum_rate(
                    branch_code
                )
            )
        else:
            if is_prepaid:
                check_value = Decimal(
                    (balances["base_balance_prepaid"] * 20) / 100
                )
            else:
                check_value = Decimal(
                    (balances["base_balance_postpaid"] * 20) / 100
                )

        if is_prepaid:
            current_balance = balances["current_balance_prepaid"]
            base_balance = balances["base_balance_prepaid"]
            should_return = \
                balances["base_balance_prepaid"] - total_cost > check_value
            return_balance = \
                balances["used_balance_prepaid"] - total_cost
        else:
            current_balance = balances["current_balance_postpaid"]
            base_balance = balances["base_balance_postpaid"]
            should_return = \
                balances["base_balance_postpaid"] - total_cost > check_value
            return_balance = \
                balances["used_balance_postpaid"] - total_cost
        if should_return:
            BasicService.add_balance(
                subscription_code,
                return_balance,
                is_prepaid,
            )
            BasicService.renew_thresholds(
                branch_code,
                subscription_code,
                base_balance,
                int(return_balance) + int(current_balance),
                is_prepaid,
            )
            return False

        return True

    @classmethod
    def _total_unpaid_active(cls, subscription_code):
        """
        Get the usages from ActiveSessions based on subscription code
        :param subscription_code:
        :return:
        """
        sessions = BasicService.get_active_sessions(subscription_code)
        cost = Decimal(0)
        for session in sessions:
            cost += Decimal(session['cost'])

        return cost

    @classmethod
    def _total_unpaid_usages(cls, subscription_code, is_prepaid):
        """
        Get total unpaid costs from CDRs
        :param subscription_code:
        :return:
        """
        start_date = None
        if is_prepaid:
            try:
                start_date = PackageInvoice.objects.filter(
                    subscription__subscription_code=subscription_code,
                    status_code=invoice_config.STATE_CHOICES[2][0],
                    is_active=True,
                    is_expired=False,
                ).latest('created_at').updated_status_at + timedelta(
                    microseconds=1
                )
            except PackageInvoice.DoesNotExist:
                pass
        else:
            try:
                start_date = Invoice.objects.filter(
                    subscription__subscription_code=subscription_code,
                    status_code=invoice_config.STATE_CHOICES[2][0],
                ).latest('created_at').created_at + timedelta(microseconds=1)
            except Invoice.DoesNotExist:
                pass

        cgr_usage = cls.calculate_usages_minimal(
            subscription_code,
            start_date,
        )

        if is_prepaid:
            return cgr_usage["cost_prepaid"]
        return cgr_usage["cost_postpaid"]
