# --------------------------------------------------------------------------
# Pseudo-service for payment that does not work with Payment gateways and
# only uses their data. Payment gateway must be handled outside of CGG.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - payment.py
# Created at 2020-8-29,  17:34:53
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime

from django.utils.translation import gettext as _

from cgg.apps.finance.models import (
    BaseBalanceInvoice,
    CreditInvoice,
    Invoice,
    PackageInvoice,
    Payment,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.payment import (
    PaymentExportSerializer,
    PaymentSerializer,
    PaymentsSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.credit_invoice import (
    CreditInvoiceService,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools

PaymentStateChoices = FinanceConfigurations.Payment.STATE_CHOICES
InvoiceStateChoices = FinanceConfigurations.Invoice.STATE_CHOICES


class PaymentService:

    @classmethod
    def get_payments(
            cls,
            customer_code,
            subscription_code,
            credit_invoice_id,
            base_balance_invoice_id,
            package_invoice_id,
            invoice_id,
            request,
            export_type=FinanceConfigurations.Export.Format.JSON,
    ):
        """
        Get details of all payments based on filters
        :param export_type:
        :param invoice_id:
        :type invoice_id:
        :param package_invoice_id:
        :type package_invoice_id:
        :param base_balance_invoice_id:
        :type base_balance_invoice_id:
        :param customer_code:
        :param subscription_code:
        :param credit_invoice_id:
        :param request:
        :return:
        """
        query_params = request.query_params
        if base_balance_invoice_id or package_invoice_id or invoice_id:
            # These items are not connected directly to payments
            other_conditions = CommonService.base_invoice_conditions(
                customer_code,
                subscription_code,
            )
            if base_balance_invoice_id:
                try:
                    related_invoice = BaseBalanceInvoice.objects.get(
                        id=base_balance_invoice_id,
                        **other_conditions,
                    )
                except BaseBalanceInvoice.DoesNotExist:
                    raise api_exceptions.NotFound404(
                        ErrorMessages.BASE_BALANCE_INVOICE_404
                    )
            elif package_invoice_id:
                try:
                    related_invoice = PackageInvoice.objects.get(
                        id=package_invoice_id,
                        **other_conditions,
                    )
                except PackageInvoice.DoesNotExist:
                    raise api_exceptions.NotFound404(
                        ErrorMessages.PACKAGE_INVOICE_404
                    )
            else:
                try:
                    related_invoice = Invoice.objects.get(
                        id=invoice_id,
                        **other_conditions,
                    )
                except Invoice.DoesNotExist:
                    raise api_exceptions.NotFound404(
                        ErrorMessages.INVOICE_404
                    )
            if related_invoice.status_code != \
                    FinanceConfigurations.Invoice.STATE_CHOICES[2][0]:
                raise api_exceptions.Conflict409(
                    ErrorMessages.PAYMENT_409_RELATED
                )
            try:
                credit_invoice = CreditInvoice.objects.get(
                    operation_type=
                    FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
                    used_for=related_invoice.credit_invoice.used_for,
                    used_for_id=related_invoice.credit_invoice.used_for_id,
                    status_code=related_invoice.credit_invoice.status_code,
                )
            except CreditInvoice.DoesNotExist:
                raise api_exceptions.Conflict409(
                    ErrorMessages.PAYMENT_409_CREDIT
                )
            query_payment = credit_invoice.payments.all()
        else:
            other_conditions = CommonService.payment_conditions(
                customer_code=customer_code,
                subscription_code=subscription_code,
                credit_invoice_id=credit_invoice_id,
            )
            query_payment = Payment.objects.filter(
                **other_conditions,
            )

        if query_params is not None:
            query_payment = CommonService.filter_and_order_payment(
                query_payment,
                query_params,
            )

        if FinanceConfigurations.Export.Format.is_json(export_type):
            query_payment, paginator = Paginator().paginate(
                request=request,
                queryset=query_payment,
            )
            payment_serializer = PaymentsSerializer(query_payment, many=True)
            data = payment_serializer.data, paginator
        else:
            payment_serializer = PaymentExportSerializer(
                query_payment,
                many=True,
            )
            data = payment_serializer.data

        return data

    @classmethod
    def get_payment(
            cls,
            customer_code,
            subscription_code,
            payment_id,
    ):
        """
        Get details of a payment based on its id
        :param customer_code:
        :param subscription_code:
        :param payment_id:
        :return:
        """
        Tools.uuid_validation(payment_id)
        other_conditions = CommonService.payment_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            payment_object = Payment.objects.get(
                id=payment_id,
                **other_conditions,
            )
        except Payment.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PAYMENT_404,
            )

        payment_serializer = PaymentSerializer(payment_object)

        return payment_serializer.data

    @classmethod
    def add_payment(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Add a new payment for a CreditInvoice
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        payment_serializer = PaymentSerializer(data=body)
        if not payment_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                payment_serializer.errors
            )
        other_conditions = CommonService.credit_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            ci_id = Tools.uuid_validation(
                payment_serializer.validated_data['credit_invoice_id'],
            )
            CreditInvoice.objects.get(
                id=ci_id,
                **other_conditions,
            )
        except CreditInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.CREDIT_INVOICE_404,
            )

        payment_serializer.save()

        return payment_serializer.data

    @classmethod
    def update_payment(
            cls,
            customer_code,
            subscription_code,
            payment_id,
            body,
    ):
        """
        Update a payment based on new status_code. if payment succeeds
        its related object (CreditInvoice) is going to update as well.
        This method removes payment cool down as well
        :param customer_code:
        :param subscription_code:
        :param payment_id:
        :param body:
        :return:
        """
        Tools.uuid_validation(payment_id)
        other_conditions = CommonService.payment_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            payment_object = Payment.objects.get(
                id=payment_id,
                **other_conditions,
            )
        except Payment.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PAYMENT_404,
            )

        credit_invoice_object = payment_object.credit_invoice

        if credit_invoice_object.status_code not in (
                InvoiceStateChoices[0][0],
                InvoiceStateChoices[1][0],
        ):
            raise api_exceptions.Conflict409(
                _("Can not pay this credit invoice due to its status_code")
            )
        if payment_object.gateway == FinanceConfigurations.Payment.OFFLINE:
            raise api_exceptions.PermissionDenied403(
                _("Can not update offline payments directly")
            )
        body = Tools.get_dict_from_json(body)
        payment_serializer = PaymentSerializer(
            payment_object,
            data=body,
            partial=True,
        )
        if not payment_serializer.is_valid():
            valid_status_codes = []
            for sts in PaymentStateChoices:
                valid_status_codes.append(sts[0])
            valid_status_codes = '/'.join(
                valid_status_codes,
            )
            error_message = ErrorMessages.VALID_CHOICES_400
            raise api_exceptions.ValidationError400(
                {
                    'status_code': f"{error_message}: {valid_status_codes}"
                }
            )
        payment_serializer.save()
        # Update cool down checking
        if payment_serializer.data['gateway'] not in (
                FinanceConfigurations.Payment.OFFLINE,
        ):
            if credit_invoice_object.used_for:
                if credit_invoice_object.used_for == \
                        FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                    invoice_class = Invoice
                elif credit_invoice_object.used_for == \
                        FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                    invoice_class = BaseBalanceInvoice
                else:
                    invoice_class = PackageInvoice
                try:
                    related_invoice = invoice_class.objects.get(
                        id=credit_invoice_object.used_for_id
                    )
                except invoice_class.DoesNotExist:
                    raise api_exceptions.NotFound404(
                        f"{ErrorMessages.GENERIC_404}"
                    )
                related_invoice.pay_cool_down = None
                related_invoice.save()
            else:
                credit_invoice_object.pay_cool_down = None
                credit_invoice_object.save()

        payment_data = payment_serializer.data
        payment_data['should_enable'] = cls.update_credit_invoice_status(
            credit_invoice_object,
            payment_data['status_code']
        )

        return payment_data

    @classmethod
    def payment_approval(
            cls,
            payment_id,
            body,
    ):
        """
        Approve an offline payment
        :param payment_id:
        :param body:
        :return:
        """
        Tools.uuid_validation(payment_id)
        try:
            payment_object = Payment.objects.get(
                id=payment_id
            )
        except Payment.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PAYMENT_404,
            )
        credit_invoice_object = payment_object.credit_invoice

        if payment_object.gateway != FinanceConfigurations.Payment.OFFLINE:
            raise api_exceptions.PermissionDenied403(
                _("Can not approve/reject the payment this due to gateway")
            )

        if credit_invoice_object.status_code != InvoiceStateChoices[1][0]:
            raise api_exceptions.Conflict409(
                _("Can not approve/reject the payment of this credit "
                  "invoice due to credits status")
            )

        body = Tools.get_dict_from_json(body)
        payment_serializer = PaymentSerializer(
            payment_object,
            data=body,
            partial=True,
        )
        if not payment_serializer.is_valid():
            valid_status_codes = []
            for sts in PaymentStateChoices:
                valid_status_codes.append(sts[0])
            valid_status_codes = '/'.join(
                valid_status_codes,
            )
            error_message = ErrorMessages.VALID_CHOICES_400
            raise api_exceptions.ValidationError400(
                {
                    'status_code': f"{error_message}: {valid_status_codes}"
                }
            )
        payment_serializer.save()
        payment_data = payment_serializer.data
        payment_data['should_enable'] = cls.update_credit_invoice_status(
            credit_invoice_object,
            payment_data['status_code']
        )

        return payment_data

    @classmethod
    def update_credit_invoice_status(
            cls,
            credit_invoice_object,
            status_code,
    ):
        """
        Change the state on payments related credit invoice based on
        payments status_code and update subscription's credit if necessary
        Caution: do not use this method before updating payments (only after
        payment_approval or update_payment)
        :param credit_invoice_object:
        :param status_code:
        :return:
        """
        # Check payment status_code and update credit invoice
        if status_code in (
                PaymentStateChoices[1][0],
                PaymentStateChoices[2][0],
        ):
            return_data = True
            change_date = datetime.now()
            credit_invoice_object.updated_status_at = change_date
            if status_code == PaymentStateChoices[1][0]:
                # Successful pay
                credit_invoice_object.paid_at = change_date
                credit_invoice_object.status_code = InvoiceStateChoices[2][0]
            else:
                # Failed pay
                credit_invoice_object.status_code = InvoiceStateChoices[0][0]
                return_data = False

            credit_invoice_object.save()
            # Update credit invoice
            CreditInvoiceService.increase_credit(credit_invoice_object)

            return return_data
