# --------------------------------------------------------------------------
# Handle logics related to BaseBalanceInvoice objects.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - base_balance_invoice.py
# Created at 2020-8-29,  16:46:16
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import (
    BaseBalanceInvoice,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.base_balance_invoice import (
    BaseBalanceInvoiceExportSerializer,
    BaseBalanceInvoiceSerializer,
    BaseBalanceInvoicesSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.customer import CustomerService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools

InvoiceStateChoices = FinanceConfigurations.Invoice.STATE_CHOICES


class BaseBalanceInvoiceService:

    @classmethod
    def get_invoice(
            cls,
            customer_code,
            subscription_code,
            base_balance,
    ):
        """
        Get a base balance invoice with all the details
        :param customer_code:
        :param subscription_code:
        :param base_balance:
        :return:
        """
        Tools.uuid_validation(base_balance)
        other_conditions = CommonService.base_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            query_invoice = BaseBalanceInvoice.objects.get(
                id=base_balance,
                **other_conditions,
            )
        except BaseBalanceInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.BASE_BALANCE_INVOICE_404,
            )

        invoice_serializer = BaseBalanceInvoiceSerializer(query_invoice)

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
        Get all base balance invoices based on query params
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
        query_invoice = BaseBalanceInvoice.objects.filter(
            **other_conditions,
        )

        if query_params is not None:
            query_invoice = CommonService.filter_and_order_base_invoice(
                BaseBalanceInvoice,
                query_invoice,
                query_params,
            )

        if FinanceConfigurations.Export.Format.is_json(export_type):
            query_invoice, paginator = Paginator().paginate(
                request=request,
                queryset=query_invoice,
            )
            invoice_serializer = BaseBalanceInvoicesSerializer(
                query_invoice,
                many=True,
            )
            data = invoice_serializer.data, paginator
        else:
            invoice_serializer = BaseBalanceInvoiceExportSerializer(
                query_invoice,
                many=True,
            )
            data = invoice_serializer.data

        return data

    @classmethod
    def issue_invoice(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Issue a new base balance invoice based on user's request
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        operation_types = FinanceConfigurations.CreditInvoice.OPERATION_TYPES
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
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
        invoice_data = Tools.get_dict_from_json(body)
        invoice_data['subscription_id'] = subscription_object.id

        bbi_serializer = BaseBalanceInvoiceSerializer(
            data=invoice_data,
        )
        if not bbi_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                bbi_serializer.errors
            )
        bbi_data = bbi_serializer.validated_data
        if bbi_data['operation_type'] == operation_types[1][0]:
            # A decrease, check for subscription's base balance
            balance_details = BasicService.get_balance(
                subscription_code=subscription_object.subscription_code,
                force_reload=True,
            )
            base_balance = Decimal(
                balance_details['base_balance_postpaid']
            )
            current_balance = Decimal(
                balance_details['current_balance_postpaid']
            )
            if Decimal(base_balance) < Decimal(bbi_data['total_cost']):
                raise api_exceptions.ValidationError400({
                    'total_cost': ErrorMessages.BASE_BALANCE_INVOICE_409
                })
            if Decimal(current_balance) < Decimal(bbi_data['total_cost']):
                raise api_exceptions.ValidationError400({
                    'value': ErrorMessages.BASE_BALANCE_INVOICE_409_CURRENT,
                })

        with transaction.atomic():
            cls.check_latest_invoice(
                subscription_object=subscription_object,
                operation_type=bbi_data['operation_type'],
            )
            bbi_serializer.save()

            if bbi_data['operation_type'] == operation_types[1][0]:
                # Decrease from base balance and add to credit if necessary
                BasicService.decrease_base_postpaid(
                    subscription_object.branch.branch_code,
                    subscription_object.subscription_code,
                    bbi_data['total_cost'],
                )
                if bbi_data['to_credit']:
                    # Increase credit after decreasing base balance
                    CustomerService.no_pay_increase_credit(
                        subscription_object.customer,
                        bbi_data['total_cost'],
                        _(
                            "This credit invoice is generated automatically "
                            "for increasing customer's credit after "
                            "decreasing it's base balance"
                        )
                    )

            return bbi_serializer.data

    @classmethod
    def check_latest_invoice(
            cls,
            subscription_object,
            operation_type,
    ):
        """
        Check for latest invoice and revoke it if possible (Use it in atomic
        transactions)
        :param subscription_object:
        :param operation_type:
        :return:
        """
        try:
            latest_invoice = BaseBalanceInvoice.objects.filter(
                subscription=subscription_object,
                operation_type=operation_type,
            ).select_for_update().latest(
                'created_at',
            )
        except BaseBalanceInvoice.DoesNotExist:
            latest_invoice = None

        if latest_invoice:
            # Cool down checking
            if latest_invoice.pay_cool_down \
                    and latest_invoice.pay_cool_down > datetime.now():
                raise api_exceptions.Conflict409(
                    ErrorMessages.PAYMENT_409_COOL_DOWN_PREVIOUS,
                )
            # Change status_code to revoke if not success
            if latest_invoice.status_code != InvoiceStateChoices[2][0]:
                latest_invoice.status_code = InvoiceStateChoices[3][0]
                latest_invoice.updated_status_at = datetime.now()
                latest_invoice.save()
