# --------------------------------------------------------------------------
# Handle renewing, expiring and other logics for PackageInvoice objects
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - package_invoice.py
# Created at 2020-8-29,  17:33:3
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import (
    PackageInvoice,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.package_invoice import (
    PackageInvoiceExportSerializer,
    PackageInvoiceSerializer,
    PackageInvoicesSerializer,
)
from cgg.apps.finance.versions.v1.services.branch import BranchService
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.credit_invoice import (
    CreditInvoiceService,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools

InvoiceStateChoices = FinanceConfigurations.Invoice.STATE_CHOICES


class PackageInvoiceService:

    @classmethod
    def get_invoice(
            cls,
            customer_code,
            subscription_code,
            package_invoice,
    ):
        """
        Get details of a package invoice based on id
        :param customer_code:
        :param subscription_code:
        :param package_invoice:
        :return:
        """
        Tools.uuid_validation(package_invoice)
        other_conditions = CommonService.base_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            query_invoice = PackageInvoice.objects.get(
                id=package_invoice,
                **other_conditions,
            )
        except PackageInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PACKAGE_INVOICE_404,
            )

        invoice_serializer = PackageInvoiceSerializer(query_invoice)

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
        Get all package invoices based on subscription, customer and filters
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
        query_invoice = PackageInvoice.objects.filter(
            **other_conditions,
        )

        if query_params is not None:
            query_invoice = CommonService.filter_and_order_base_invoice(
                PackageInvoice,
                query_invoice,
                query_params,
            )

        if FinanceConfigurations.Export.Format.is_json(export_type):
            query_invoice, paginator = Paginator().paginate(
                request=request,
                queryset=query_invoice,
            )
            invoice_serializer = PackageInvoicesSerializer(
                query_invoice,
                many=True,
            )
            data = invoice_serializer.data, paginator
        else:
            invoice_serializer = PackageInvoiceExportSerializer(
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
        Issue a new package invoice for a subscription
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        if subscription_object.subscription_type == \
                FinanceConfigurations.Subscription.TYPE[2][0]:
            raise api_exceptions.Conflict409(
                ErrorMessages.SUBSCRIPTION_409_UNLIMITED
            )

        invoice_data = Tools.get_dict_from_json(body)
        invoice_data['subscription_id'] = subscription_object.id
        if PackageInvoice.objects.filter(
                subscription=subscription_object,
                is_active=True,
        ).count() > 0:
            raise api_exceptions.Conflict409(
                ErrorMessages.PACKAGE_INVOICE_409,
            )

        package_invoice_serializer = PackageInvoiceSerializer(
            data=invoice_data,
        )
        if not package_invoice_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                package_invoice_serializer.errors
            )
        with transaction.atomic():
            try:
                latest_invoice = PackageInvoice.objects.filter(
                    subscription=subscription_object
                ).select_for_update().latest(
                    'created_at',
                )
            except PackageInvoice.DoesNotExist:
                latest_invoice = None

            if latest_invoice is not None:
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

            package_invoice_serializer.save()
            response_data = package_invoice_serializer.data

            return response_data

    @classmethod
    def update_package_invoice(
            cls,
            customer_code,
            subscription_code,
            package_invoice,
            body,
    ):
        """
        Update a package invoice's "auto_renew"
        :param customer_code:
        :param subscription_code:
        :param package_invoice:
        :param body:
        :return:
        """
        Tools.uuid_validation(package_invoice)
        body = Tools.get_dict_from_json(body)
        other_conditions = CommonService.base_invoice_conditions(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        try:
            invoice_object = PackageInvoice.objects.get(
                id=package_invoice,
                **other_conditions,
            )
        except PackageInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.PACKAGE_INVOICE_404,
            )

        invoice_serializer = PackageInvoiceSerializer(
            invoice_object,
            data=body,
            partial=True,
        )

        if invoice_serializer.is_valid(raise_exception=True):
            invoice_serializer.save()

            return invoice_serializer.data

    @classmethod
    def disable_active_package(cls, subscription_code):
        """
        Disable the active package of a subscription
        :param subscription_code:
        :return:
        """
        try:
            package_invoice = PackageInvoice.objects.filter(
                subscription__subscription_code=subscription_code,
                is_active=True,
            ).latest('created_at')
        except PackageInvoice.DoesNotExist:
            return False

        package_invoice.is_active = False
        package_invoice.save()

    @classmethod
    def expire_prepaid(cls, subscription_code):
        """
        Expire a prepaid package (Expire date or max usage). Renew it if
        subscription has enough credit
        :param subscription_code:
        :return:
        """
        # 1. Get active package invoices
        try:
            package_invoice = PackageInvoice.objects.filter(
                subscription__subscription_code=subscription_code,
                is_active=True,
            ).latest('created_at')
        except PackageInvoice.DoesNotExist:
            return False

        current_prepaid_balance = BasicService.get_balance(
            package_invoice.subscription.subscription_code,
            force_reload=True,
        )['current_balance_prepaid']
        temp = package_invoice.total_value - current_prepaid_balance
        expired_value = package_invoice.total_value - temp
        maximum_rate = BasicService.get_branch_maximum_rate(
            package_invoice.subscription.branch.branch_code,
        )
        if Decimal(expired_value) <= Decimal(maximum_rate):
            expired_value = 0
        package_invoice.expired_value = expired_value
        package_invoice.is_active = False
        package_invoice.is_expired = True
        package_invoice.save()
        # Renew base balance of prepaid balance
        CreditInvoiceService.change_base_prepaid_in_cgrates(
            package_invoice.subscription.branch.branch_code,
            package_invoice.subscription.subscription_code,
            base_amount=package_invoice.total_value,
            change_amount=expired_value,
            is_increase=False,
        )
        # Remove action plan if exists (Maybe this is 100% usage expiry)
        BasicService.remove_action_plan_balance_expiry(
            package_invoice.subscription.subscription_code,
        )
        # Auto renew checking
        is_renewed = cls.renew_prepaid(package_invoice)
        # Check for active packages and end prepaid if no packages is active
        if PackageInvoice.objects.filter(
                subscription=package_invoice.subscription,
                is_active=True,
        ).count() == 0:
            BasicService.set_balance(
                subscription_code,
                value=None,
                is_prepaid=False,
            )
            BasicService.set_attribute_profile_account(
                package_invoice.subscription.subscription_code,
                package_invoice.subscription.number,
                FinanceConfigurations.Subscription.TYPE[0][0],
                package_invoice.subscription.branch.branch_code,
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                BranchService.get_emergency_destinations(),
            )

        return is_renewed

    @classmethod
    def renew_prepaid(cls, package_invoice):
        """
        Renew prepaid based on previous invoice's auto renew filed
        :param package_invoice:
        :return:
        """
        if package_invoice.auto_renew and Decimal(
                package_invoice.subscription.customer.credit
        ) >= Decimal(package_invoice.package.package_price):
            # Create an identical package invoice
            if package_invoice.package:
                expiry_date = CommonService.get_expired_at(
                    package_invoice.package.package_due,
                )
            else:
                expiry_date = CommonService.get_expired_at(
                    FinanceConfigurations.Package.TYPES[5][0],
                )
            new_invoice = PackageInvoice()
            new_invoice.subscription = package_invoice.subscription
            new_invoice.package = package_invoice.package
            new_invoice.expired_at = expiry_date
            new_invoice.updated_status_at = datetime.now()
            new_invoice.total_cost = package_invoice.package.package_price
            new_invoice.total_value = package_invoice.package.package_value
            new_invoice.auto_renew = package_invoice.auto_renew
            new_invoice.is_active = False
            new_invoice.description = _(
                "This package invoice is generated automatically due to auto "
                "renewal setting of previous invoice"
            )
            new_invoice.status_code = \
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0]
            new_invoice.save()
            # Use credit service's decrease
            CreditInvoiceService.decrease_credit(
                customer_object=new_invoice.subscription.customer,
                used_for=FinanceConfigurations.CreditInvoice.USED_FOR[2][0],
                used_for_id=new_invoice.id,
                description=_(
                    "This credit invoice is generated automatically due to "
                    "auto renewal setting of a package invoice"
                )
            )

            return True

        return False
