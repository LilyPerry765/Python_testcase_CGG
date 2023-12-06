# --------------------------------------------------------------------------
# Handles increase/decrease CreditInvoices and their related objects
# (BaseBalanceInvoice/Invoice/PackageInvoice) and other basic logics for
# CreditInvoices
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - credit_invoice.py
# Created at 2020-8-29,  17:13:28
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import (
    datetime,
)
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import (
    BaseBalanceInvoice,
    CreditInvoice,
    Customer,
    Invoice,
    PackageInvoice,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.credit_invoice import (
    CreditInvoiceExportSerializer,
    CreditInvoiceSerializer,
    CreditInvoicesSerializer,
)
from cgg.apps.finance.versions.v1.services.branch import BranchService
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools

InvoiceStateChoices = FinanceConfigurations.Invoice.STATE_CHOICES


class CreditInvoiceService:

    @classmethod
    def get_invoice(
            cls,
            customer_code,
            subscription_code,
            credit_invoice,
    ):
        """
        Get all credit invoices based on subscription, customer and id
        :param customer_code:
        :param subscription_code:
        :param credit_invoice:
        :return:
        """
        Tools.uuid_validation(credit_invoice)
        other_conditions = CommonService.credit_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            query_invoice = CreditInvoice.objects.get(
                id=credit_invoice,
                **other_conditions,
            )
        except CreditInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.CREDIT_INVOICE_404,
            )

        invoice_serializer = CreditInvoiceSerializer(query_invoice)

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
        Get all credit invoices based on customer, subscription and query
        params
        :param export_type:
        :param customer_code:
        :param subscription_code:
        :param request:
        :return:
        """
        query_params = request.query_params
        other_conditions = CommonService.credit_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        query_invoice = CreditInvoice.objects.filter(
            **other_conditions,
        )

        if query_params is not None:
            query_invoice = CommonService.filter_and_order_base_invoice(
                CreditInvoice,
                query_invoice,
                query_params,
            )

        if FinanceConfigurations.Export.Format.is_json(export_type):
            query_invoice, paginator = Paginator().paginate(
                request=request,
                queryset=query_invoice,
            )
            invoice_serializer = CreditInvoicesSerializer(
                query_invoice,
                many=True,
            )
            data = invoice_serializer.data, paginator
        else:
            invoice_serializer = CreditInvoiceExportSerializer(
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
        Issue a new credit invoices based on decrease and increase
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        if customer_code is None:
            subscription_object = CommonService.get_subscription_object(
                customer_code=customer_code,
                subscription_code=subscription_code,
            )
            if subscription_object.subscription_type == \
                    FinanceConfigurations.Subscription.TYPE[2][0]:
                raise api_exceptions.Conflict409(
                    ErrorMessages.SUBSCRIPTION_409_UNLIMITED
                )
            customer_object = subscription_object.customer
        else:
            try:
                customer_object = Customer.objects.get(
                    customer_code=customer_code
                )
            except Customer.DoesNotExist:
                raise api_exceptions.NotFound404(
                    ErrorMessages.CUSTOMER_404
                )
        invoice_data = Tools.get_dict_from_json(body)
        invoice_data['customer_id'] = customer_object.id
        ci_serializer = CreditInvoiceSerializer(
            data=invoice_data,
        )
        if not ci_serializer.is_valid():
            raise api_exceptions.ValidationError400(ci_serializer.errors)

        with transaction.atomic():
            cls.check_latest_invoice(
                customer_object,
                used_for=ci_serializer.validated_data['used_for'] if
                'used_for' in ci_serializer.validated_data else None
            )
            if ci_serializer.validated_data['operation_type'] == \
                    FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0]:
                # Decrease and return data
                response_data = cls.decrease_credit(
                    customer_object=customer_object,
                    used_for=ci_serializer.data['used_for'],
                    used_for_id=ci_serializer.data['used_for_id'],
                )
            else:
                # Increase and return data
                ci_serializer.save()
                response_data = ci_serializer.data

            return response_data

    @classmethod
    def increase_credit(cls, ci_obj: CreditInvoice):
        """
        Increase credit of subscription for a successfully payed credit
        invoice. Also responsible for handling automatic decrease of credit
        using decrease_credit method
        :param ci_obj: CreditInvoice object
        :type ci_obj: CreditInvoice
        :return:
        :rtype:
        """
        if ci_obj.status_code == InvoiceStateChoices[2][0]:
            # Update subscription's credit
            ci_obj.customer.credit += ci_obj.total_cost
            ci_obj.customer.save()

            if ci_obj.used_for in (
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0],
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0],
                    FinanceConfigurations.CreditInvoice.USED_FOR[2][0],
            ):
                # Decrease if it's used for another invoice
                cls.decrease_credit(
                    ci_obj.customer,
                    ci_obj.used_for,
                    ci_obj.used_for_id,
                    _(
                        "This credit invoice is generated automatically to "
                        "pay for an existing invoice",
                    )
                )

    @classmethod
    def decrease_credit(
            cls,
            customer_object: Customer,
            used_for: str,
            used_for_id: str,
            description='',
    ):
        """
        Creates an 'decrease' CreditInvoice, decrease subscription's
        credit and handle invoice/base-balance-invoice/package-invoice
        status updates.
        :param customer_object:
        :type customer_object: Customer
        :param used_for:
        :type used_for: str
        :param used_for_id:
        :type used_for_id: str
        :param description:
        :type description:
        :return:
        :rtype:
        """
        if not used_for_id and not used_for:
            raise api_exceptions.Conflict409(
                ErrorMessages.CREDIT_INVOICE_409
            )

        decrease_credit_dict = {
            'customer_id': customer_object.id,
            'used_for': used_for,
            'used_for_id': used_for_id,
            'operation_type':
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
            'description': description,
        }
        decrease_credit_serializer = CreditInvoiceSerializer(
            data=decrease_credit_dict,
        )
        credit_invoice_object = None
        if decrease_credit_serializer.is_valid(raise_exception=True):
            if Decimal(customer_object.credit) < Decimal(
                    decrease_credit_serializer.validated_data['total_cost']
            ):
                raise api_exceptions.Conflict409(
                    ErrorMessages.SUBSCRIPTION_409_CREDIT,
                )
            decrease_credit_serializer.save()
            # Get credit invoice's object
            credit_invoice_object = CreditInvoice.objects.get(
                id=decrease_credit_serializer.data['id']
            )
            # Change invoice|base-balance-invoice|package-invoice status
            if credit_invoice_object.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                # This is an invoice
                try:
                    invoice_object = Invoice.objects.get(
                        id=credit_invoice_object.used_for_id,
                        status_code__in=[
                            InvoiceStateChoices[0][0],
                            InvoiceStateChoices[1][0],
                        ]
                    )
                except Invoice.DoesNotExist:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.INVOICE_404_PAY,
                    )
                if invoice_object.subscription.subscription_type in (
                        FinanceConfigurations.Subscription.TYPE[0][0],
                        FinanceConfigurations.Subscription.TYPE[1][0],
                ):
                    # Prepaid or Postpaid
                    if invoice_object.subscription.subscription_type == \
                            FinanceConfigurations.Subscription.TYPE[0][0]:
                        # Increase postpaid balance if subscription is postpaid
                        total_usage_cost_before = \
                            cls.get_previous_total_usage_costs(
                                invoice_object.id
                            )
                        if BasicService.add_balance(
                                invoice_object.subscription.subscription_code,
                                total_usage_cost_before,
                                is_prepaid=False,
                        ):
                            base_balance = \
                                BasicService.get_base_balance_postpaid(
                                    invoice_object.subscription.subscription_code,
                                    True,
                                )
                            current_balance_postpaid = \
                                BasicService.get_balance(
                                    invoice_object.subscription.subscription_code,
                                    True,
                                )['current_balance_postpaid']
                            BasicService.renew_thresholds(
                                invoice_object.subscription.branch.branch_code,
                                invoice_object.subscription.subscription_code,
                                base_balance,
                                current_balance_postpaid,
                                is_prepaid=False,
                            )
                    # Common process for postpaid and prepaid
                    invoice_object.paid_at = datetime.now()
                    invoice_object.status_code = InvoiceStateChoices[2][0]
                    invoice_object.updated_status_at = datetime.now()
                    invoice_object.credit_invoice = credit_invoice_object
                    invoice_object.save()
                    # Paying an invoice should update due_date_notified
                    Invoice.objects.filter(
                        subscription=invoice_object.subscription,
                        due_date_notified=False,
                        invoice_type_code=
                        FinanceConfigurations.Invoice.TYPES[0][0],
                    ).update(
                        due_date_notified=True,
                    )
                    # Update subscription latest paid
                    invoice_object.subscription.update_latest_payed()
            elif credit_invoice_object.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                # Used for BaseBalanceInvoice object
                try:
                    bb_invoice_object = BaseBalanceInvoice.objects.get(
                        id=credit_invoice_object.used_for_id,
                        status_code__in=[
                            InvoiceStateChoices[0][0],
                            InvoiceStateChoices[1][0],
                        ]
                    )
                except BaseBalanceInvoice.DoesNotExist:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.BASE_BALANCE_INVOICE_404_PAY,
                    )
                if BasicService.increase_base_postpaid(
                        bb_invoice_object.subscription.branch.branch_code,
                        bb_invoice_object.subscription.subscription_code,
                        credit_invoice_object.total_cost,
                ):
                    bb_invoice_object.paid_at = datetime.now()
                    bb_invoice_object.status_code = InvoiceStateChoices[2][0]
                    bb_invoice_object.updated_status_at = datetime.now()
                    bb_invoice_object.credit_invoice = credit_invoice_object
                    bb_invoice_object.save()
            elif credit_invoice_object.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[2][0]:
                # Used for PackageInvoice object
                try:
                    package_invoice = PackageInvoice.objects.get(
                        id=credit_invoice_object.used_for_id,
                        status_code__in=[
                            InvoiceStateChoices[0][0],
                            InvoiceStateChoices[1][0],
                        ]
                    )
                except PackageInvoice.DoesNotExist:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.PACKAGE_INVOICE_404_PAY,
                    )
                if PackageInvoice.objects.filter(
                        subscription=package_invoice.subscription,
                        is_active=True,
                ).count() > 0:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.PACKAGE_INVOICE_409,
                    )
                if package_invoice.package:
                    expiry_date = CommonService.get_expired_at(
                        package_invoice.package.package_due,
                    )
                else:
                    expiry_date = CommonService.get_expired_at(
                        FinanceConfigurations.Package.TYPES[5][0],
                    )
                if cls.make_balances_prepaid(
                        package_invoice.subscription.branch.branch_code,
                        package_invoice.subscription.subscription_code,
                        package_invoice.subscription.number,
                        package_invoice.total_value,
                        expiry_date,
                ):
                    package_invoice.paid_at = datetime.now()
                    package_invoice.status_code = InvoiceStateChoices[2][0]
                    package_invoice.updated_status_at = datetime.now()
                    package_invoice.credit_invoice = credit_invoice_object
                    package_invoice.is_active = True
                    package_invoice.expired_at = expiry_date
                    package_invoice.save()

            # Change credit invoice's status
            credit_invoice_object.status_code = InvoiceStateChoices[2][0]
            credit_invoice_object.updated_status_at = datetime.now()
            credit_invoice_object.save()
            # Decrease credit from customer
            customer_object.credit -= credit_invoice_object.total_cost
            customer_object.save()

        if credit_invoice_object:
            # Serialize based on updated object
            credit_invoice_serializer = CreditInvoiceSerializer(
                credit_invoice_object
            )
            return credit_invoice_serializer.data

    @classmethod
    def get_previous_total_usage_costs(cls, invoice_id):
        """
        Get total usage cost of all unpaid invoices from this invoice
        backwards till a successful invoice
        :param invoice_id: id of an Invoice object
        :type invoice_id: uuid
        :return: total cost of Invoice object
        :rtype: Decimal
        """
        total_usage_cost = Decimal(0)
        try:
            latest_invoice = Invoice.objects.get(id=invoice_id)
            total_usage_cost = Decimal(latest_invoice.total_usage_cost)
        except Invoice.DoesNotExist:
            return total_usage_cost

        # Get previous successful invoice
        try:
            previous_date = Invoice.objects.filter(
                status_code=InvoiceStateChoices[2][0],
                created_at__lt=latest_invoice.created_at,
                subscription=latest_invoice.subscription,
            ).latest('created_at').created_at
        except Invoice.DoesNotExist:
            previous_date = None

        # Get all revoked invoices before
        if previous_date is not None:
            revoked_invoices = Invoice.objects.filter(
                status_code=InvoiceStateChoices[3][0],
                created_at__gt=previous_date,
                created_at__lt=latest_invoice.created_at,
                subscription=latest_invoice.subscription,
            )
        else:
            revoked_invoices = Invoice.objects.filter(
                status_code=InvoiceStateChoices[3][0],
                created_at__lt=latest_invoice.created_at,
                subscription=latest_invoice.subscription,
            )

        for revoked_invoice in revoked_invoices:
            total_usage_cost += Decimal(revoked_invoice.total_usage_cost)

        return total_usage_cost

    @classmethod
    def make_balances_prepaid(
            cls,
            branch_code,
            subscription_code,
            number,
            total_value,
            expiry_date,
    ):
        """
        Make *prepaid balance True and *postpaid balance to False and change
        base balance of prepaid balance based on total value
        :param number:
        :param branch_code:
        :param subscription_code:
        :param total_value:
        :param expiry_date:
        :return:
        """
        BasicService.set_balance(
            subscription_code=subscription_code,
            value=None,
            is_prepaid=True,
            expiry_date=expiry_date,
        )
        cls.change_base_prepaid_in_cgrates(
            branch_code,
            subscription_code,
            base_amount=total_value,
            change_amount=total_value,
            is_increase=True,
        )
        BasicService.set_attribute_profile_account(
            subscription_code,
            number,
            FinanceConfigurations.Subscription.TYPE[1][0],
            branch_code,
            FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
            BranchService.get_emergency_destinations(),
        )

        return True

    @classmethod
    def change_base_prepaid_in_cgrates(
            cls,
            branch_code,
            subscription_code,
            base_amount,
            change_amount,
            is_increase,
    ):
        """
        Increase and decrease based on change_amount and base_amount
        :param change_amount:
        :param base_amount:
        :param is_increase: boolean
        :param branch_code:
        :param subscription_code:
        :return:
        """
        current_base = BasicService.get_base_balance_prepaid(
            subscription_code,
            True,
        )
        # 0. Renew base balance
        if is_increase:
            new_base_balance = Decimal(current_base) + Decimal(base_amount)
        else:
            new_base_balance = Decimal(current_base) - Decimal(base_amount)
        BasicService.apply_base_balance(
            branch_code,
            subscription_code,
            new_base_balance,
            is_prepaid=True,
        )
        # 1. Debit or add new value to account
        if is_increase:
            # Add
            if Decimal(change_amount) > 0:
                BasicService.add_balance(
                    subscription_code,
                    change_amount,
                    is_prepaid=True,
                )
        else:
            # Debit
            if Decimal(change_amount) > 0:
                BasicService.debit_balance(
                    subscription_code,
                    change_amount,
                    is_prepaid=True,
                )

        return False

    @classmethod
    def check_latest_invoice(
            cls,
            customer_object,
            used_for,
    ):
        """
        Check for latest invoice and revoke it if possible (Use it in atomic
        transactions)
        :param customer_object:
        :param used_for:
        :return:
        """
        try:
            latest_invoice = CreditInvoice.objects.filter(
                customer=customer_object,
                used_for=used_for,
            ).select_for_update().latest('created_at')
        except CreditInvoice.DoesNotExist:
            latest_invoice = None

        if latest_invoice is not None:
            # Cool down checking
            if latest_invoice.pay_cool_down \
                    and latest_invoice.pay_cool_down > datetime.now():
                raise api_exceptions.Conflict409(
                    ErrorMessages.PAYMENT_409_COOL_DOWN_PREVIOUS,
                )
            # Change status_code to revoke if not success or pending
            if latest_invoice.status_code not in (
                    InvoiceStateChoices[1][0],
                    InvoiceStateChoices[2][0],
            ):
                latest_invoice.status_code = InvoiceStateChoices[3][0]
                latest_invoice.updated_status_at = datetime.now()
                latest_invoice.save()
