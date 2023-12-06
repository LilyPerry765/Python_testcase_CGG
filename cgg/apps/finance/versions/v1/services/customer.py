# --------------------------------------------------------------------------
# Handle logics related to Customer objects.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - customer.py
# Created at 2020-8-29,  17:15:10
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext as _

from cgg.apps.finance.models import CreditInvoice, Customer
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.credit_invoice import (
    IncreaseCreditSerializer,
)
from cgg.apps.finance.versions.v1.serializers.customer import (
    CustomerSerializer,
    CustomersSerializer,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.credit_invoice import (
    CreditInvoiceService,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools


class CustomerService:

    @classmethod
    def add_customer(
            cls,
            body,
    ):
        """
        Creates a new customer with a unique code
        customer_code is the customer's id (primary key) in trunk backend.
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        customer_serializer = CustomerSerializer(data=body)
        if customer_serializer.is_valid(raise_exception=True):
            customer_serializer.save()

        return customer_serializer.data

    @classmethod
    def get_customer(cls, customer_code):
        """
        Get the details of a customer
        :param customer_code:
        :return:
        """
        try:
            customer_object = Customer.objects.get(
                customer_code=customer_code
            )
        except Customer.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.CUSTOMER_404,
            )

        customer_serializer = CustomerSerializer(customer_object)

        return customer_serializer.data

    @classmethod
    def get_customers(cls, request):
        """
        Get all customers with filters
        :param request:
        :return:
        """
        query_params = request.query_params
        customer_objects = Customer.objects.all()

        if query_params is not None:
            # All filters in customers
            if any(
                    item in ['customer_code', 'prime_code'] for item in
                    query_params
            ):
                code = query_params[
                    'prime_code'] if 'prime_code' in query_params else \
                    query_params['customer_code']
                customer_objects = customer_objects.filter(
                    customer_code__icontains=code,
                )

            if 'customer_codes' in query_params:
                customer_codes = [
                    e.strip() for e in
                    query_params['customer_codes'].split(',')
                ]
                customer_objects = customer_objects.filter(
                    customer_code__in=customer_codes
                )

            # Order by
            customer_objects = CommonService.order_by_query(
                Customer,
                customer_objects,
                query_params,
            )

        customer_objects, paginator = Paginator().paginate(
            request=request,
            queryset=customer_objects,
        )
        customers_serializer = CustomersSerializer(
            customer_objects,
            many=True,
        )

        return customers_serializer.data, paginator

    @classmethod
    def no_pay_increase_credit(
            cls,
            customer_object,
            value,
            desc,
            used_for=None,
            used_for_id=None,
    ):
        """
        Increase subscription's credit without payment
        :param customer_object:
        :param value:
        :param desc:
        :param used_for: if not None (with used_for_id), decrease immediately
        :param used_for_id: read used_for
        :return:
        """
        with transaction.atomic():
            CreditInvoiceService.check_latest_invoice(
                customer_object,
                used_for=used_for,
            )
            credit_invoice_object = CreditInvoice()
            credit_invoice_object.customer = customer_object
            credit_invoice_object.updated_status_at = datetime.now()
            credit_invoice_object.paid_at = datetime.now()
            credit_invoice_object.status_code = \
                FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
            credit_invoice_object.total_cost = Decimal(value)
            credit_invoice_object.description = desc
            credit_invoice_object.used_for = used_for
            credit_invoice_object.used_for_id = used_for_id
            credit_invoice_object.save()
            customer_object.credit += credit_invoice_object.total_cost
            customer_object.save()
            if used_for and used_for_id:
                CreditInvoiceService.decrease_credit(
                    customer_object=customer_object,
                    used_for=used_for,
                    used_for_id=used_for_id,
                    description=desc,
                )

    @classmethod
    def increase_credit_customer(
            cls,
            customer_code,
            subscription_code,
            body=''
    ):
        """
        Increase the credit of a customer (without payment)
        :param customer_code:
        :param subscription_code:
        :param body: IncreaseCreditSerializer
        :return:
        """
        credit = None
        if body:
            credit = Tools.get_dict_from_json(body)
            credit_serializer = IncreaseCreditSerializer(
                data=credit,
            )
            if credit_serializer.is_valid(raise_exception=True):
                credit = credit_serializer.data['credit']
        if customer_code is None:
            subscription_object = CommonService.get_subscription_object(
                customer_code=customer_code,
                subscription_code=subscription_code,
            )
            customer_object = subscription_object.customer
        else:
            try:
                customer_object = Customer.objects.get(
                    customer_code=customer_code,
                )
            except Customer.DoesNotExist:
                raise api_exceptions.NotFound404(ErrorMessages.CUSTOMER_404)

        if credit is None:
            raise api_exceptions.ValidationError400({
                'non_fields': ErrorMessages.JSON_BODY_400
            })

        cls.no_pay_increase_credit(
            customer_object,
            credit,
            _(
                "This credit invoice is generated automatically for "
                "increasing customer's credit without payment"
            )
        )

        return True
