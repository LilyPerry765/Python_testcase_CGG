# --------------------------------------------------------------------------
# All API related functions for finance app. Use log_api_request decorator
# to log each request.
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - api.py
# Created at 2020-5-16,  11:55:50
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.utils.translation import gettext as _
from rest_framework import exceptions, status
from rest_framework.views import APIView

from cgg.apps.finance.apps import FinanceConfig
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.base_balance_invoice import (
    BaseBalanceInvoiceService,
)
from cgg.apps.finance.versions.v1.services.branch import BranchService
# Shared tasks using Celery
from cgg.apps.finance.versions.v1.services.cgrates_notify import (
    handle_cgrates_expired_notification,
    handle_cgrates_notification,
)
from cgg.apps.finance.versions.v1.services.credit_invoice import (
    CreditInvoiceService,
)
from cgg.apps.finance.versions.v1.services.customer import (
    CustomerService,
)
from cgg.apps.finance.versions.v1.services.destination import (
    DestinationService,
)
from cgg.apps.finance.versions.v1.services.invoice import (
    InvoiceService,
)
from cgg.apps.finance.versions.v1.services.migrations import (
    MigrationsService,
)
from cgg.apps.finance.versions.v1.services.operator import (
    OperatorService,
)
from cgg.apps.finance.versions.v1.services.package import PackageService
from cgg.apps.finance.versions.v1.services.package_invoice import (
    PackageInvoiceService,
)
from cgg.apps.finance.versions.v1.services.payment import (
    PaymentService,
)
from cgg.apps.finance.versions.v1.services.profit import ProfitService
from cgg.apps.finance.versions.v1.services.runtime_config import (
    RuntimeConfigService,
)
from cgg.apps.finance.versions.v1.services.subscription import (
    SubscriptionService,
)
from cgg.core.decorators import log_api_request
from cgg.core.error_messages import ErrorMessages
from cgg.core.permissions import TrunkBackendAPIPermission
from cgg.core.response import csv_response, response
from cgg.core.tools import Tools

APILabels = FinanceConfigurations.APIRequestLabels


class CustomersAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_CUSTOMERS,
    )
    def get(self, request, *args, **kwargs):
        try:
            data = CustomerService.get_customers(request)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of customers'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_CUSTOMER,
    )
    def post(self, request, *args, **kwargs):
        try:
            data = CustomerService.add_customer(request.body)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new customer is created successfully'),
        )


class CustomerAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_CUSTOMER,
    )
    def get(self, request, customer, *args, **kwargs):
        try:
            response_data = CustomerService.get_customer(customer)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Details of a customer'),
        )


class SubscriptionsAntiAPIView(APIView):
    """
    This is an anti pattern of REST API design, I know :)
    @TODO: Remove this
    """
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_SUBSCRIPTIONS_ANTI,
    )
    def get(self, request, customer=None, *args, **kwargs):
        try:
            data = SubscriptionService.get_subscriptions_anti(
                customer,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of subscriptions'),
        )


class SubscriptionsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_SUBSCRIPTIONS,
    )
    def get(self, request, customer=None, *args, **kwargs):
        try:
            data = SubscriptionService.get_subscriptions(
                customer,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of subscriptions'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_SUBSCRIPTION,
    )
    def post(self, request, customer=None, *args, **kwargs):
        try:
            data = SubscriptionService.create_subscription(
                customer,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new subscription is created successfully'),
        )


class SubscriptionAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_SUBSCRIPTION,
    )
    def get(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            data = SubscriptionService.get_subscription(
                customer,
                subscription,
                request.query_params,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a subscription'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_SUBSCRIPTION,
    )
    def patch(
            self,
            request,
            customer=None,
            subscription=None,
    ):
        try:
            data = SubscriptionService.update_subscription(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Used and base balance are updated successfully'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.REMOVE_SUBSCRIPTION,
    )
    def delete(
            self,
            request,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            SubscriptionService.remove_subscription(
                customer,
                subscription,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class SubscriptionAvailabilityAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_SUBSCRIPTION_AVAILABILITY,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            response_data = SubscriptionService.get_availability_subscription(
                customer,
                subscription,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Subscription availability status'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.CHANGE_SUBSCRIPTION_AVAILABILITY,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            response_data = \
                SubscriptionService.change_availability_subscription(
                    customer,
                    subscription,
                    request.body,
                )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Subscription availability changed successfully'),
        )


class SubscriptionDeallocateAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.SUBSCRIPTION_DEALLOCATE,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
    ):
        try:
            # Issuing interim invoice is async. this may lead to problems
            # with deallocating because we issue invoices only for allocated
            # subscriptions'
            InvoiceService.issue_interim_invoice(
                customer,
                subscription,
                description=_(
                    "This invoice is generated automatically before "
                    "deallocating the subscription"
                ),
                bypass_type=
                FinanceConfigurations.Invoice.BypassType.DEALLOCATE,
                on_demand=False,
            )
            print('after issue_interim_invoice')
            response_data = SubscriptionService.deallocate_subscription(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            print(str(e.detail))
            print(str(e.status_code))
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Subscription deallocate successfully'),
        )


class SubscriptionDebitBalanceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.SUBSCRIPTION_DEBIT_BALANCE,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            response_data = \
                SubscriptionService.debit_balance_from_subscription(
                    customer,
                    subscription,
                    request.body,
                )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_("Subscription's balance debited successfully"),
        )


class SubscriptionAddBalanceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.SUBSCRIPTION_ADD_BALANCE,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            response_data = \
                SubscriptionService.add_balance_from_subscription(
                    customer,
                    subscription,
                    request.body,
                )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_("Subscription's balance added successfully"),
        )


class SubscriptionConvertAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=
        APILabels.UPDATE_SUBSCRIPTION_CONVERT,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
    ):
        try:
            response_data = SubscriptionService.convert_subscription(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_("Subscription converted to postpaid successfully"),
        )


class SubscriptionIncreaseCreditAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=
        APILabels.INCREASE_CUSTOMER_CREDIT,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
    ):
        try:
            response_data = CustomerService.increase_credit_customer(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_("Customer's credit increased successfully"),
        )


class SubscriptionChangeBaseBalanceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=
        APILabels.CHANGE_SUBSCRIPTION_BASE_BALANCE,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
    ):
        try:
            response_data = \
                SubscriptionService.change_base_balance_subscription(
                    customer,
                    subscription,
                    request.body,
                )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_("Subscription's base balance changed successfully"),
        )


class PackageAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PACKAGE,
    )
    def get(
            self,
            request,
            package,
            *args,
            **kwargs,
    ):
        try:
            data = PackageService.get_package(
                package,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a package'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_PACKAGE,
    )
    def patch(
            self,
            request,
            package,
    ):
        try:
            data = PackageService.update_package(
                package,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Package updated successfully'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.REMOVE_PACKAGE,
    )
    def delete(
            self,
            request,
            package,
            *args,
            **kwargs,
    ):
        try:
            PackageService.remove_package(package)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class PackagesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PACKAGES,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            data = PackageService.get_packages(
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('All packages'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_PACKAGE,
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            data = PackageService.add_package(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new package is created successfully'),
        )


class ExportInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPORT_INVOICES,
    )
    def get(
            self,
            request,
            export_type,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            data = InvoiceService.get_invoices(
                customer,
                subscription,
                request,
                export_type,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return export_csv(request, 'invoices', data)


class InvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_INVOICES,
    )
    def get(self, request, customer=None, subscription=None, *args, **kwargs):
        """
        List all invoices for a subscription
        """
        try:
            data = InvoiceService.get_invoices(
                customer,
                subscription,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of invoices'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.CREATE_INTERIM_INVOICE,
    )
    def post(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            on_demand = False
            message = _("Created on admin's demand")
            if 'on_demand' in request.query_params:
                on_demand = True
                message = _("Created on customer's demand")
            InvoiceService.issue_interim_invoice(
                customer_code=customer,
                subscription_code=subscription,
                description=message,
                on_demand=on_demand,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_202_ACCEPTED,
            message=_('A new interim invoice will be created if possible'),
        )


class InvoiceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_INVOICE,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            invoice=None,
            *args,
            **kwargs,
    ):
        """
        Details of an invoice
        """
        try:
            data = InvoiceService.get_invoice(
                customer,
                subscription,
                invoice,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of an invoice'),
        )


class MigrateInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.MIGRATE_INVOICES,
    )
    def post(self, request, *args, **kwargs):
        try:
            data = MigrationsService.migrate_invoices(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Migration of invoices'),
        )


class ExportBaseBalanceInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPORT_BASE_BALANCE_INVOICES,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            export_type=FinanceConfigurations.Export.Format.CSV,
            *args,
            **kwargs,
    ):
        try:
            data = BaseBalanceInvoiceService.get_invoices(
                customer,
                subscription,
                request,
                export_type,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return export_csv(request, 'base-balance-invoices', data)


class BaseBalanceInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_BASE_BALANCE_INVOICES,
    )
    def get(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            data = BaseBalanceInvoiceService.get_invoices(
                customer,
                subscription,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of base balance invoices'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.CREATE_BASE_BALANCE_INVOICE,
    )
    def post(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            response_data = BaseBalanceInvoiceService.issue_invoice(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=response_data,
            message=_('A new base balance invoice is created successfully'),
        )


class BaseBalanceInvoiceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_BASE_BALANCE_INVOICE,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            base_balance=None,
            *args,
            **kwargs,
    ):
        """
        Details of an invoice
        """
        try:
            data = BaseBalanceInvoiceService.get_invoice(
                customer,
                subscription,
                base_balance,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a base balance invoice'),
        )


class MigrateBaseBalanceInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=
        APILabels.MIGRATE_BASE_BALANCE_INVOICES,
    )
    def post(self, request, *args, **kwargs):
        try:
            data = MigrationsService.migrate_base_balance_invoices(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Migration of base balance invoices'),
        )


class ExportPackageInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPORT_PACKAGE_INVOICES,
    )
    def get(
            self,
            request,
            export_type,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            data = PackageInvoiceService.get_invoices(
                customer,
                subscription,
                request,
                export_type
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return export_csv(request, 'package-invoices', data)


class PackageInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PACKAGE_INVOICES,
    )
    def get(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            data = PackageInvoiceService.get_invoices(
                customer,
                subscription,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of package invoices'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.CREATE_PACKAGE_INVOICE,
    )
    def post(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            response_data = PackageInvoiceService.issue_invoice(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=response_data,
            message=_('A new package invoice is created successfully'),
        )


class PackageInvoiceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PACKAGE_INVOICE,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            package_invoice=None,
            *args,
            **kwargs,
    ):
        try:
            data = PackageInvoiceService.get_invoice(
                customer,
                subscription,
                package_invoice,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a package invoice'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_PACKAGE_INVOICE,
    )
    def patch(
            self,
            request,
            customer=None,
            subscription=None,
            package_invoice=None,
    ):
        try:
            data = PackageInvoiceService.update_package_invoice(
                customer,
                subscription,
                package_invoice,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Package invoice is updated successfully'),
        )


class ExportCreditInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPORT_CREDIT_INVOICES,
    )
    def get(
            self,
            request,
            export_type,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            data = CreditInvoiceService.get_invoices(
                customer,
                subscription,
                request,
                export_type,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return export_csv(request, 'credit-invoices', data)


class CreditInvoicesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_CREDIT_INVOICES,
    )
    def get(self, request, customer=None, subscription=None, *args, **kwargs):
        """
        List all credit invoices for a subscription
        """
        try:
            data = CreditInvoiceService.get_invoices(
                customer,
                subscription,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of credit invoices'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.CREATE_CREDIT_INVOICE,
    )
    def post(self, request, customer=None, subscription=None, *args, **kwargs):
        try:
            response_data = CreditInvoiceService.issue_invoice(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=response_data,
            message=_('A new credit invoice is created successfully'),
        )


class CreditInvoiceAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_CREDIT_INVOICE,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            credit=None,
            *args,
            **kwargs,
    ):
        """
        Details of an invoice
        """
        try:
            data = CreditInvoiceService.get_invoice(
                customer,
                subscription,
                credit,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a credit invoice'),
        )


class PaymentsExportAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPORT_PAYMENTS,
    )
    def get(
            self,
            request,
            export_type,
            customer=None,
            subscription=None,
            credit_invoice=None,
            base_balance_invoice=None,
            package_invoice=None,
            invoice=None,
            *args,
            **kwargs,
    ):
        try:
            data = PaymentService.get_payments(
                customer,
                subscription,
                credit_invoice,
                base_balance_invoice,
                package_invoice,
                invoice,
                request,
                export_type,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return export_csv(request, 'payments', data)


class PaymentsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PAYMENTS,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            credit_invoice=None,
            base_balance_invoice=None,
            package_invoice=None,
            invoice=None,
            *args,
            **kwargs,
    ):
        try:
            data = PaymentService.get_payments(
                customer,
                subscription,
                credit_invoice,
                base_balance_invoice,
                package_invoice,
                invoice,
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of payments'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_PAYMENT,
    )
    def post(
            self,
            request,
            customer=None,
            subscription=None,
            *args,
            **kwargs,
    ):
        try:
            data = PaymentService.add_payment(
                customer,
                subscription,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new payment is created successfully'),
        )


class PaymentAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PAYMENT,
    )
    def get(
            self,
            request,
            customer=None,
            subscription=None,
            payment=None,
            *args,
            **kwargs,
    ):
        try:
            data = PaymentService.get_payment(
                customer,
                subscription,
                payment,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a payment'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_PAYMENT,
    )
    def patch(
            self,
            request,
            customer=None,
            subscription=None,
            payment=None,
    ):
        try:
            data = PaymentService.update_payment(
                customer,
                subscription,
                payment,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Payment updated successfully'),
        )


class PaymentApprovalAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.APPROVE_PAYMENT,
    )
    def post(
            self,
            request,
            payment,
            *args,
            **kwargs,
    ):
        try:
            data = PaymentService.payment_approval(
                payment,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Payment approval updated successfully'),
        )


class BranchesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_BRANCHES,
    )
    def get(self, request, *args, **kwargs):
        try:
            data = BranchService.get_branches(request)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of branches'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_BRANCH,
    )
    def post(self, request, *args, **kwargs):
        try:
            data = BranchService.add_branch(request.body)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new branch is created successfully'),
        )


class BranchAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_BRANCH,
    )
    def get(self, request, branch_id, *args, **kwargs):
        try:
            response_data = BranchService.get_branch(branch_id)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Details of a branch'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_BRANCH,
    )
    def patch(self, request, branch_id):
        try:
            response_data = BranchService.update_branch(
                branch_id,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Branch updated successfully'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.DELETE_BRANCH,
    )
    def delete(self, request, branch_id, *args, **kwargs):
        try:
            BranchService.remove_branch(
                branch_id,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class DestinationsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_DESTINATIONS,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            data = DestinationService.get_destinations(
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of destinations'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_DESTINATION,
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = DestinationService.add_destination(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=response_data,
            message=_('A new destination is created successfully'),
        )


class DestinationsNamesAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_DESTINATIONS_NAMES,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            data = DestinationService.get_destination_names(
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of destinations by names'),
        )


class DestinationAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_DESTINATION,
    )
    def get(
            self,
            request,
            destination,
            *args,
            **kwargs,
    ):
        try:
            response_data = DestinationService.get_destination(
                destination,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Details of a destination'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.REMOVE_DESTINATION,
    )
    def delete(
            self,
            request,
            destination,
            *args,
            **kwargs,
    ):
        try:
            DestinationService.remove_destination(
                destination,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_DESTINATION,
    )
    def patch(
            self,
            request,
            destination,
    ):
        try:
            response_data = DestinationService.update_destination(
                destination,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Destination updated successfully'),
        )


class OperatorsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_OPERATORS,
    )
    def get(self, request, *args, **kwargs):
        try:
            data = OperatorService.get_operators(
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of operators'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_OPERATOR,
    )
    def post(self, request, *args, **kwargs):
        try:
            data = OperatorService.add_operator(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new operator is created successfully'),
        )


class OperatorAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_OPERATOR,
    )
    def get(self, request, operator, *args, **kwargs):
        try:
            data = OperatorService.get_operator(
                operator,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of an operator'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_OPERATOR,
    )
    def patch(self, request, operator):
        try:
            data = OperatorService.update_operator(
                operator,
                request.body
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Operator updated successfully'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.DELETE_OPERATOR,
    )
    def delete(self, request, operator, *args, **kwargs):
        try:
            OperatorService.remove_operator(
                operator,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class ExportProfitsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPORT_PROFITS,
    )
    def get(self, request, export_type, *args, **kwargs):
        try:
            data = ProfitService.get_profits(
                request,
                export_type,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return export_csv(request, 'profits', data)


class ProfitsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PROFITS,
    )
    def get(self, request, *args, **kwargs):
        try:
            data = ProfitService.get_profits(
                request,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of profits'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.ADD_PROFIT,
    )
    def post(self, request, *args, **kwargs):
        try:
            data = ProfitService.add_profit(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_201_CREATED,
            data=data,
            message=_('A new profit is created successfully'),
        )


class ProfitAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_PROFIT,
    )
    def get(self, request, profit, *args, **kwargs):
        try:
            data = ProfitService.get_profit(
                profit,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Details of a profit'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_PROFIT,
    )
    def patch(self, request, profit, *args, **kwargs):
        try:
            data = ProfitService.update_profit(
                profit,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=data,
            message=_('Profit is updated successfully'),
        )


class CGRateSExpiryAPIView(APIView):
    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.EXPIRY_NOTIFICATION,
    )
    def post(self, request, subscription_code, *args, **kwargs):
        handle_cgrates_expired_notification.delay(
            subscription_code
        )
        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('A new expiry notification received from CGRateS'),
        )


class CGRateSNotificationAPIView(APIView):
    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.USAGE_NOTIFICATION,
    )
    def post(self, request, notify_type, *args, **kwargs):
        body = Tools.get_dict_from_json(request.body)
        handle_cgrates_notification.delay(
            notify_type,
            body,
        )
        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('A new notification received from CGRateS'),
        )


class RuntimeConfigsAPIView(APIView):
    permission_classes = (TrunkBackendAPIPermission,)

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.GET_RUNTIME_CONFIGS,
    )
    def get(self, request, *args, **kwargs):
        try:
            response_data = RuntimeConfigService.get()
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Details of Runtime Configs'),
        )

    @log_api_request(
        app_name=FinanceConfig.name,
        label=APILabels.UPDATE_RUNTIME_CONFIGS,
    )
    def patch(self, request, *args, **kwargs):
        try:
            response_data = RuntimeConfigService.update(request.body)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_200_OK,
            data=response_data,
            message=_('Runtime Configs updated successfully'),
        )


def export_csv(request, name, data):
    """
    Export data to csv format with proper naming
    :param request:
    :type request:
    :param name:
    :type name:
    :param data:
    :type data:
    :return:
    :rtype:
    """
    if len(data) == 0:
        return response(
            request,
            error=ErrorMessages.EXPORT_NO_DATA,
            status=status.HTTP_404_NOT_FOUND,
        )
    file_name = Tools.get_file_name(name)

    return csv_response(data, file_name)
