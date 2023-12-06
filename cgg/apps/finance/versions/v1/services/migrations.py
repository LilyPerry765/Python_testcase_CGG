# --------------------------------------------------------------------------
# Serves as a middleman between services to avoid circular import
# problem for migrating from old service to new
# Must be deprecated and removed in later versions (+0.9.0)!
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - migrations.py
# Created at 2020-3-31,  17:7:29
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
import uuid
from decimal import Decimal

from django.utils.translation import gettext as _

from cgg.apps.finance.models import (
    BaseBalanceInvoice,
    CreditInvoice,
    Invoice,
    Payment,
    Subscription,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.base_balance_invoice import (
    MigrateBaseBalanceInvoiceSerializer,
)
from cgg.apps.finance.versions.v1.serializers.credit_invoice import (
    MigrateCreditInvoiceSerializer,
)
from cgg.apps.finance.versions.v1.serializers.invoice import (
    MigrateInvoiceSerializer
)
from cgg.apps.finance.versions.v1.services.invoice import (
    InvoiceService
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.tools import Tools

PaymentStateChoices = FinanceConfigurations.Payment.STATE_CHOICES


class MigrationsService:

    @classmethod
    def create_increase_credit_invoice(
            cls,
            customer_id,
            used_for,
            used_for_id,
            updated_at,
    ):
        """
        This method is only used in InvoiceService and BaseBalanceService
        migrations to migrate payed invoices without having an effect on
        CGRateS and any other side effects so use it once and wise
        :param updated_at:
        :type updated_at:
        :param customer_id:
        :type customer_id:
        :param used_for:
        :type used_for:
        :param used_for_id:
        :type used_for_id:
        :return:
        :rtype:
        """
        increase_credit_dict = {
            'customer_id': customer_id,
            'used_for': used_for,
            'used_for_id': used_for_id,
            'operation_type':
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
            'description': _(
                "This credit invoice is migrated automatically from old "
                "payments system",
            ),
        }
        credit_invoice_serializer = MigrateCreditInvoiceSerializer(
            data=increase_credit_dict,
        )
        if credit_invoice_serializer.is_valid(raise_exception=True):
            try:
                latest_invoice = CreditInvoice.objects.filter(
                    customer__id=customer_id
                ).latest(
                    'created_at',
                )
            except CreditInvoice.DoesNotExist:
                latest_invoice = None

            if latest_invoice is not None:
                # change status_code to revoke if not success
                if latest_invoice.status_code != \
                        FinanceConfigurations.Invoice.STATE_CHOICES[2][0]:
                    latest_invoice.status_code = \
                        FinanceConfigurations.Invoice.STATE_CHOICES[3][0]
                    latest_invoice.updated_status_at = updated_at
                    latest_invoice.save()

            credit_invoice_serializer.save()

            return CreditInvoice.objects.get(
                id=credit_invoice_serializer.data['id']
            )

    @classmethod
    def create_decrease_credit_invoice(
            cls,
            credit_invoice_id,
            created_at,
            updated_at,
    ):
        """
        This method is only used in InvoiceService and BaseBalanceService
        migrations to migrate payed invoices without having an effect on
        CGRateS and any other side effects so use it once and wise
        :param credit_invoice_id:
        :type credit_invoice_id:
        :param created_at:
        :type created_at:
        :param updated_at:
        :type updated_at:
        :return:
        :rtype:
        """
        try:
            increase_credit_invoice_object = CreditInvoice.objects.get(
                id=credit_invoice_id
            )
        except CreditInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.CREDIT_INVOICE_404,
            )
        increase_credit_invoice_object.paid_at = updated_at
        increase_credit_invoice_object.status_code = \
            FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
        increase_credit_invoice_object.save()

        if increase_credit_invoice_object.used_for in (
                FinanceConfigurations.CreditInvoice.USED_FOR[0][0],
                FinanceConfigurations.CreditInvoice.USED_FOR[1][0],
        ):
            # Migrate decrease credit
            decrease_credit_dict = {
                'customer_id':
                    increase_credit_invoice_object.customer.id,
                'used_for': increase_credit_invoice_object.used_for,
                'used_for_id': increase_credit_invoice_object.used_for_id,
                'total_cost': increase_credit_invoice_object.total_cost,
                'operation_type':
                    FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
                'description': _(
                    "This credit invoice is migrated automatically from old "
                    "payments system",
                ),
            }
            decrease_credit_serializer = MigrateCreditInvoiceSerializer(
                data=decrease_credit_dict,
            )

            if decrease_credit_serializer.is_valid(raise_exception=True):
                decrease_credit_serializer.save()
                # Get credit invoice's object
                decrease_credit_invoice_object = CreditInvoice.objects.get(
                    id=decrease_credit_serializer.data['id']
                )
                # Change invoice/base-balance-invoice status
                if decrease_credit_invoice_object.used_for == \
                        FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                    try:
                        invoice_object = Invoice.objects.get(
                            id=decrease_credit_invoice_object.used_for_id,
                        )
                    except Invoice.DoesNotExist:
                        raise api_exceptions.Conflict409(
                            ErrorMessages.INVOICE_404_PAY,
                        )
                    invoice_object.paid_at = updated_at
                    invoice_object.status_code = \
                        FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
                    invoice_object.updated_status_at = updated_at
                    invoice_object.credit_invoice = \
                        decrease_credit_invoice_object
                    invoice_object.save()
                elif decrease_credit_invoice_object.used_for == \
                        FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                    try:
                        base_balance_invoice_object = \
                            BaseBalanceInvoice.objects.get(
                                id=decrease_credit_invoice_object.used_for_id,
                            )
                    except BaseBalanceInvoice.DoesNotExist:
                        raise api_exceptions.Conflict409(
                            ErrorMessages.BASE_BALANCE_INVOICE_404_PAY,
                        )
                    base_balance_invoice_object.paid_at = updated_at
                    base_balance_invoice_object.status_code = \
                        FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
                    base_balance_invoice_object.updated_status_at = updated_at
                    base_balance_invoice_object.credit_invoice = \
                        decrease_credit_invoice_object
                    base_balance_invoice_object.save()

                # Change credit invoice's status
                decrease_credit_invoice_object.status_code = \
                    FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
                decrease_credit_invoice_object.updated_status_at = updated_at
                decrease_credit_invoice_object.save()

                CreditInvoice.objects.filter(
                    id=decrease_credit_invoice_object.id).update(
                    updated_at=updated_at,
                    created_at=created_at,
                )

    @classmethod
    def migrate_invoices(cls, body):
        """
        Migrate invoices from antique database to CGG
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        migrate_invoices_serializer = MigrateInvoiceSerializer(
            data=body,
            many=True,
        )

        if migrate_invoices_serializer.is_valid(raise_exception=True):
            migrate_invoices = migrate_invoices_serializer.validated_data
            for migrate_invoice in migrate_invoices:
                try:
                    subscription_object = Subscription.objects.get(
                        subscription_code=migrate_invoice['subscription_code'],
                    )
                except Subscription.DoesNotExist:
                    subscription_object = None
                if subscription_object:
                    try:
                        latest_invoice = Invoice.objects.filter(
                            subscription__subscription_code=migrate_invoice[
                                'subscription_code']).latest(
                            'created_at',
                        )
                    except Invoice.DoesNotExist:
                        latest_invoice = None
                    invoice_object = Invoice()
                    if latest_invoice:
                        invoice_object.period_count = int(
                            latest_invoice.period_count) + 1
                    else:
                        invoice_object.period_count = int(1)
                    invoice_object.subscription = subscription_object
                    invoice_object.subscription_fee = migrate_invoice[
                        'subscription_fee']
                    invoice_object.tax_cost = migrate_invoice['tax_cost']
                    invoice_object.tax_percent = migrate_invoice['tax_percent']
                    invoice_object.debt = migrate_invoice['debt']
                    invoice_object.mobile_cost = migrate_invoice['mobile_cost']
                    invoice_object.mobile_usage = migrate_invoice[
                        'mobile_usage']
                    invoice_object.landlines_long_distance_cost = \
                        migrate_invoice[
                            'landlines_long_distance_cost']
                    invoice_object.landlines_long_distance_usage = \
                        migrate_invoice[
                            'landlines_long_distance_usage']
                    invoice_object.description = migrate_invoice['description']
                    invoice_object.invoice_type_code = migrate_invoice[
                        'invoice_type']
                    invoice_object.status_code = migrate_invoice['status_code']
                    invoice_object.from_date = migrate_invoice['from_date']
                    invoice_object.to_date = migrate_invoice['to_date']
                    invoice_object.created_at = migrate_invoice['created_at']
                    invoice_object.updated_at = migrate_invoice['updated_at']
                    invoice_object.discount = Decimal(
                        migrate_invoice['discount']
                    )
                    invoice_object.updated_status_at = migrate_invoice[
                        'updated_at']
                    invoice_object.tracking_code = uuid.uuid4()
                    invoice_object.due_date = InvoiceService.get_due_date(
                        migrate_invoice['invoice_type'],
                    )
                    invoice_object.landlines_local_cost = Decimal(0)
                    invoice_object.landlines_local_usage = Decimal(0)
                    invoice_object.landlines_corporate_cost = Decimal(0)
                    invoice_object.landlines_corporate_usage = Decimal(0)
                    invoice_object.international_cost = Decimal(0)
                    invoice_object.international_usage = Decimal(0)
                    invoice_object.landlines_long_distance_cost_prepaid = \
                        Decimal(0)
                    invoice_object.landlines_long_distance_usage_prepaid = \
                        Decimal(0)
                    invoice_object.landlines_local_cost_prepaid = Decimal(0)
                    invoice_object.landlines_local_usage_prepaid = Decimal(0)
                    invoice_object.landlines_corporate_cost_prepaid = Decimal(
                        0
                    )
                    invoice_object.landlines_corporate_usage_prepaid = Decimal(
                        0
                    )
                    invoice_object.international_cost_prepaid = Decimal(0)
                    invoice_object.international_usage_prepaid = Decimal(0)
                    invoice_object.mobile_cost_prepaid = Decimal(0)
                    invoice_object.mobile_usage_prepaid = Decimal(0)
                    invoice_object.total_cost = \
                        InvoiceService.calculate_total_cost(
                            Decimal(0),
                            migrate_invoice['landlines_long_distance_cost'],
                            Decimal(0),
                            migrate_invoice['mobile_cost'],
                            Decimal(0),
                            migrate_invoice['tax_cost'],
                            migrate_invoice['subscription_fee'],
                            migrate_invoice['debt'],
                            migrate_invoice['discount'],
                        )
                    invoice_object.save()
                    if migrate_invoice['payments']:
                        credit_invoice_data = \
                            cls.create_increase_credit_invoice(
                                customer_id=subscription_object.customer.id,
                                used_for=
                                FinanceConfigurations.CreditInvoice.USED_FOR[
                                    0][0],
                                used_for_id=str(invoice_object.id),
                                updated_at=migrate_invoice['updated_at']
                            )
                        for payment in migrate_invoice['payments']:
                            payment_object = Payment()
                            payment_object.credit_invoice = credit_invoice_data
                            payment_object.status_code = payment['status_code']
                            payment_object.extra_data = payment['extra_data']
                            payment_object.amount = payment['amount']
                            payment_object.gateway = payment['gateway']
                            payment_object.updated_status_at = payment[
                                'updated_at']
                            payment_object.save()
                            invoice_object.updated_status_at = payment[
                                'updated_at']
                            if payment_object.status_code == \
                                    PaymentStateChoices[1][0]:
                                cls.create_decrease_credit_invoice(
                                    credit_invoice_id=credit_invoice_data.id,
                                    created_at=migrate_invoice['created_at'],
                                    updated_at=payment['updated_at'],
                                )

                            CreditInvoice.objects.filter(
                                id=credit_invoice_data.id).update(
                                created_at=migrate_invoice['created_at'],
                                updated_at=payment['updated_at'],
                            )
                            Payment.objects.filter(
                                id=payment_object.id).update(
                                updated_at=payment['updated_at'],
                                created_at=payment['created_at'],
                            )

                    Invoice.objects.filter(
                        id=invoice_object.id).update(
                        updated_at=migrate_invoice['updated_at'],
                        created_at=migrate_invoice['created_at'],
                    )

            return True

    @classmethod
    def migrate_base_balance_invoices(cls, body):
        """
        Migrate base balance invoices from antique database to CGG
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        migrate_base_balance_invoices_serializer = \
            MigrateBaseBalanceInvoiceSerializer(
                data=body,
                many=True,
            )

        if migrate_base_balance_invoices_serializer.is_valid(
                raise_exception=True,
        ):
            migrate_base_balance_invoices = \
                migrate_base_balance_invoices_serializer.validated_data

            for migrate_base_balance_invoice in migrate_base_balance_invoices:
                try:
                    subscription_object = Subscription.objects.get(
                        subscription_code=migrate_base_balance_invoice[
                            'subscription_code'],
                    )
                except Subscription.DoesNotExist:
                    subscription_object = None
                if subscription_object:
                    base_balance_invoice_object = BaseBalanceInvoice()
                    base_balance_invoice_object.subscription = \
                        subscription_object
                    base_balance_invoice_object.total_cost = \
                        migrate_base_balance_invoice['total_cost']
                    base_balance_invoice_object.status_code = \
                        migrate_base_balance_invoice['status_code']
                    base_balance_invoice_object.created_at = \
                        migrate_base_balance_invoice['created_at']
                    base_balance_invoice_object.updated_at = \
                        migrate_base_balance_invoice['updated_at']
                    base_balance_invoice_object.updated_status_at = \
                        migrate_base_balance_invoice['updated_at']
                    base_balance_invoice_object.tracking_code = uuid.uuid4()
                    base_balance_invoice_object.save()

                    if migrate_base_balance_invoice['payments']:
                        credit_invoice_data = \
                            cls.create_increase_credit_invoice(
                                customer_id=subscription_object.customer.id,
                                used_for=
                                FinanceConfigurations.CreditInvoice.USED_FOR[
                                    1][0],
                                used_for_id=str(
                                    base_balance_invoice_object.id),
                                updated_at=migrate_base_balance_invoice[
                                    'updated_at']
                            )
                        for payment in migrate_base_balance_invoice[
                            'payments']:
                            payment_object = Payment()
                            payment_object.credit_invoice = credit_invoice_data
                            payment_object.status_code = payment['status_code']
                            payment_object.extra_data = payment['extra_data']
                            payment_object.amount = payment['amount']
                            payment_object.gateway = payment['gateway']
                            payment_object.updated_status_at = payment[
                                'updated_at']
                            payment_object.save()
                            base_balance_invoice_object.updated_status_at = \
                                payment['updated_at']
                            if payment_object.status_code == \
                                    PaymentStateChoices[1][0]:
                                cls.create_decrease_credit_invoice(
                                    credit_invoice_id=credit_invoice_data.id,
                                    created_at=migrate_base_balance_invoice[
                                        'created_at'],
                                    updated_at=payment['updated_at'],
                                )

                            CreditInvoice.objects.filter(
                                id=credit_invoice_data.id).update(
                                created_at=migrate_base_balance_invoice[
                                    'created_at'],
                                updated_at=payment['updated_at'],
                            )
                            Payment.objects.filter(
                                id=payment_object.id).update(
                                updated_at=payment['updated_at'],
                                created_at=payment['created_at'],
                            )

                    BaseBalanceInvoice.objects.filter(
                        id=base_balance_invoice_object.id).update(
                        updated_at=migrate_base_balance_invoice['updated_at'],
                        created_at=migrate_base_balance_invoice['created_at'],
                    )

            return True
