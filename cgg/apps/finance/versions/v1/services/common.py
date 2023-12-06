# --------------------------------------------------------------------------
# Serves other services. We gather common functionality that are
# independent from models or services (not helpers) and put them in one
# place. The purpose here is to be DRY
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - common.py
# Created at 2020-4-7,  16:32:25
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils.translation import gettext as _

from cgg.apps.finance.models import (
    BaseBalanceInvoice,
    CreditInvoice,
    Invoice,
    PackageInvoice,
    Payment,
    Subscription,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.runtime_config import (
    RuntimeConfigService,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages


class CommonService:

    @classmethod
    def order_by_query(cls, class_object, query_object, query_params):
        """
        A Generic order by query based on query params. class_object a model
        that have model_field_exists method.
        :param class_object: A django model class
        :type class_object: class
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: An ordered django ORM query
        :rtype: object
        """
        if FinanceConfigurations.QueryParams.ORDER_BY in query_params:
            order_field_error = []
            order_by = [
                x.strip() for x in query_params
                [FinanceConfigurations.QueryParams.ORDER_BY].split(',')
            ]
            for order in order_by:
                if not class_object.model_field_exists(
                        order.replace('-', ''),
                ):
                    order_field_error.append(order)
            if order_field_error:
                raise api_exceptions.ValidationError400(
                    {
                        'non_fields': ErrorMessages.ORDER_BY_400,
                        'errors': order_field_error,
                    }
                )

            query_object = query_object.order_by(
                *order_by
            )

        return query_object

    @classmethod
    def filter_query_invoice(cls, query_object, query_params):
        """
        Filters specific for Invoice model
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        query_object = cls.filter_from_and_to_date(
            query_object,
            query_params,
        )

        if FinanceConfigurations.QueryParams.INVOICE_TYPE_CODE in query_params:
            query_object = cls._filter_invoice_type_code(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.INVOICE_TYPE_CODE
                ]
            )

        return query_object

    @classmethod
    def filter_query_base_balance_invoice(cls, query_object, query_params):
        """
        Common filters for BaseBalance model
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        if FinanceConfigurations.QueryParams.OPERATION_TYPE in query_params:
            query_object = cls._filter_invoice_operation_type(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.OPERATION_TYPE
                ]
            )

        return cls.filter_query_base_invoice(query_object, query_params)

    @classmethod
    def filter_query_base_invoice(cls, query_object, query_params):
        """
        Common filters for any models that extends BaseInvoice model
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        if FinanceConfigurations.QueryParams.GENERIC_OR in query_params:
            query_object = cls._filter_generic_or_base_invoice(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.GENERIC_OR
                ]
            )

        if FinanceConfigurations.QueryParams.SUBSCRIPTION_CODE in query_params:
            query_object = cls._filter_base_invoice_subscription_code(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.SUBSCRIPTION_CODE
                ]
            )

        if FinanceConfigurations.QueryParams.PRIME_CODE in query_params:
            query_object = cls._filter_base_invoice_customer_code(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.PRIME_CODE
                ]
            )

        if FinanceConfigurations.QueryParams.NUMBER in query_params:
            query_object = cls._filter_base_invoice_number(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.NUMBER
                ]
            )

        if FinanceConfigurations.QueryParams.PAID_AT_FROM in query_params:
            query_object = cls._filter_paid_at_from(
                query_object,
                query_params[FinanceConfigurations.QueryParams.PAID_AT_FROM]
            )

        if FinanceConfigurations.QueryParams.PAID_AT_TO in query_params:
            query_object = cls._filter_paid_at_to(
                query_object,
                query_params[FinanceConfigurations.QueryParams.PAID_AT_TO]
            )

        if FinanceConfigurations.QueryParams.TOTAL_COST_FROM in query_params:
            query_object = cls._filter_total_cost_from(
                query_object,
                query_params[FinanceConfigurations.QueryParams.TOTAL_COST_FROM]
            )

        if FinanceConfigurations.QueryParams.TOTAL_COST_TO in query_params:
            query_object = cls._filter_total_cost_to(
                query_object,
                query_params[FinanceConfigurations.QueryParams.TOTAL_COST_TO]
            )

        if FinanceConfigurations.QueryParams.TRACKING_CODE in query_params:
            query_object = cls._filter_tracking_code(
                query_object,
                query_params[FinanceConfigurations.QueryParams.TRACKING_CODE]
            )

        if FinanceConfigurations.QueryParams.STATUS_CODE in query_params:
            query_object = cls._filter_base_invoice_status_code(
                query_object,
                query_params[FinanceConfigurations.QueryParams.STATUS_CODE]
            )

        return query_object

    @classmethod
    def filter_query_credit_invoice(cls, query_object, query_params):
        """
        Common filters for CreditInvoice
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        if FinanceConfigurations.QueryParams.FRIENDLY in query_params:
            query_object = cls._filter_friendly_credit_invoice(
                query_object,
            )

        if FinanceConfigurations.QueryParams.GENERIC_OR in query_params:
            query_object = cls._filter_generic_or_credit_invoice(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.GENERIC_OR
                ]
            )

        if FinanceConfigurations.QueryParams.PRIME_CODE in query_params:
            query_object = cls._filter_credit_invoice_customer_code(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.PRIME_CODE
                ]
            )

        if FinanceConfigurations.QueryParams.SUBSCRIPTION_CODE in query_params:
            query_object = cls._filter_credit_invoice_subscription_code(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.SUBSCRIPTION_CODE
                ]
            )

        if FinanceConfigurations.QueryParams.NUMBER in query_params:
            query_object = cls._filter_credit_invoice_number(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.NUMBER
                ]
            )

        if FinanceConfigurations.QueryParams.OPERATION_TYPE in query_params:
            query_object = cls._filter_invoice_operation_type(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.OPERATION_TYPE
                ]
            )

        if FinanceConfigurations.QueryParams.PAID_AT_FROM in query_params:
            query_object = cls._filter_paid_at_from(
                query_object,
                query_params[FinanceConfigurations.QueryParams.PAID_AT_FROM]
            )

        if FinanceConfigurations.QueryParams.PAID_AT_TO in query_params:
            query_object = cls._filter_paid_at_to(
                query_object,
                query_params[FinanceConfigurations.QueryParams.PAID_AT_TO]
            )

        if FinanceConfigurations.QueryParams.TOTAL_COST_FROM in query_params:
            query_object = cls._filter_total_cost_from(
                query_object,
                query_params[FinanceConfigurations.QueryParams.TOTAL_COST_FROM]
            )

        if FinanceConfigurations.QueryParams.TOTAL_COST_TO in query_params:
            query_object = cls._filter_total_cost_to(
                query_object,
                query_params[FinanceConfigurations.QueryParams.TOTAL_COST_TO]
            )

        if FinanceConfigurations.QueryParams.TRACKING_CODE in query_params:
            query_object = cls._filter_tracking_code(
                query_object,
                query_params[FinanceConfigurations.QueryParams.TRACKING_CODE]
            )

        if FinanceConfigurations.QueryParams.STATUS_CODE in query_params:
            query_object = cls._filter_base_invoice_status_code(
                query_object,
                query_params[FinanceConfigurations.QueryParams.STATUS_CODE]
            )

        return query_object

    @classmethod
    def filter_query_common(cls, query_object, query_params):
        """
        Filter query object based on common fields in models
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        if FinanceConfigurations.QueryParams.CREATED_AT_FROM in query_params:
            query_object = cls._filter_created_at_from(
                query_object,
                query_params[FinanceConfigurations.QueryParams.CREATED_AT_FROM]
            )

        if FinanceConfigurations.QueryParams.CREATED_AT_TO in query_params:
            query_object = cls._filter_created_at_to(
                query_object,
                query_params[FinanceConfigurations.QueryParams.CREATED_AT_TO]
            )

        if FinanceConfigurations.QueryParams.UPDATED_AT_FROM in query_params:
            query_object = cls._filter_updated_at_from(
                query_object,
                query_params[FinanceConfigurations.QueryParams.UPDATED_AT_FROM]
            )

        if FinanceConfigurations.QueryParams.UPDATED_AT_TO in query_params:
            query_object = cls._filter_updated_at_to(
                query_object,
                query_params[FinanceConfigurations.QueryParams.UPDATED_AT_TO]
            )

        return query_object

    @classmethod
    def _filter_created_at_from(cls, query_object, value):
        try:
            created_at_from = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                created_at__gte=created_at_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.CREATED_AT_FROM:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_created_at_to(cls, query_object, value):
        try:
            created_at_to = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                created_at__lte=created_at_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.CREATED_AT_TO:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_updated_at_from(cls, query_object, value):
        try:
            updated_at_from = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                updated_at__gte=updated_at_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.UPDATED_AT_FROM:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_updated_at_to(cls, query_object, value):
        try:
            updated_at_to = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                updated_at__lte=updated_at_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.UPDATED_AT_TO:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_total_cost_from(cls, query_object, value):
        try:
            total_cost_from = Decimal(value)
            query_object = query_object.filter(
                total_cost__gte=total_cost_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.TOTAL_COST_FROM:
                        ErrorMessages.TOTAL_COST_400
                }
            )

        return query_object

    @classmethod
    def _filter_total_cost_to(cls, query_object, value):
        try:
            total_cost_to = Decimal(value)
            query_object = query_object.filter(
                total_cost__lte=total_cost_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.TOTAL_COST_FROM:
                        ErrorMessages.TOTAL_COST_400
                }
            )

        return query_object

    @classmethod
    def _filter_paid_at_from(cls, query_object, value):
        try:
            paid_at_from = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                paid_at__gte=paid_at_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.PAID_AT_FROM:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_paid_at_to(cls, query_object, value):
        try:
            paid_at_to = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                paid_at__lte=paid_at_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.PAID_AT_TO:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_tracking_code(cls, query_object, value):
        try:
            tracking_code_uuid = str(value)
            query_object = query_object.filter(
                tracking_code__icontains=tracking_code_uuid,
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.TRACKING_CODE:
                        ErrorMessages.TRACKING_CODE_400
                }
            )

        return query_object

    @classmethod
    def _filter_base_invoice_subscription_code(cls, query_object, value):
        query_object = query_object.filter(
            subscription__subscription_code__icontains=value,
        )

        return query_object

    @classmethod
    def _filter_base_invoice_customer_code(cls, query_object, value):
        try:
            customer_code = int(value)
        except ValueError:
            customer_code = 0
        query_object = query_object.filter(
            subscription__customer__customer_code__icontains=customer_code,
        )

        return query_object

    @classmethod
    def _filter_base_invoice_number(cls, query_object, value):
        query_object = query_object.filter(
            subscription__number__icontains=value,
        )

        return query_object

    @classmethod
    def _filter_credit_invoice_number(cls, query_object, value):
        query_object = query_object.filter(
            customer__subscriptions__number__icontains=value,
        ).distinct()

        return query_object

    @classmethod
    def _filter_invoice_operation_type(cls, query_object, value):
        if value not in (
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
        ):
            raise api_exceptions.ValidationError400({
                FinanceConfigurations.QueryParams.OPERATION_TYPE:
                    _("Not a valid operation type")
            })
        query_object = query_object.filter(
            operation_type=value,
        )

        return query_object

    @classmethod
    def _filter_credit_invoice_subscription_code(cls, query_object, value):
        query_object = query_object.filter(
            customer__subscriptions__subscription_code__icontains=value,
        ).distinct()

        return query_object

    @classmethod
    def _filter_credit_invoice_customer_code(cls, query_object, value):
        try:
            customer_code = int(value)
        except ValueError:
            customer_code = 0
        query_object = query_object.filter(
            customer__customer_code__icontains=customer_code,
        )

        return query_object

    @classmethod
    def _filter_from_date_from(cls, query_object, value):
        try:
            from_date_from = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                from_date__gte=from_date_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.FROM_DATE_FROM:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_generic_or_base_invoice(cls, query_object, value):
        """
        Generic or filter on query
        :param query_object:
        :param value: value to search for
        :return:
        """
        try:
            customer_code = int(value)
        except ValueError:
            customer_code = value
        tracking_code_uuid = str(value)
        query_object = query_object.filter(
            Q(subscription__customer__customer_code__icontains=customer_code) |
            Q(subscription__subscription_code__icontains=value) |
            Q(subscription__number__icontains=value) |
            Q(tracking_code__icontains=tracking_code_uuid)
        ).distinct()

        return query_object

    @classmethod
    def _filter_friendly_credit_invoice(cls, query_object):
        """
        Make credit invoices result user friendly
        :param query_object:
        :return:
        """
        query_object = query_object.filter(
            Q(
                used_for__isnull=False,
                status_code=FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
            ) |
            Q(used_for__isnull=True)
        ).distinct()

        return query_object

    @classmethod
    def _filter_generic_or_credit_invoice(cls, query_object, value):
        """
        Generic or filter on query
        :param query_object:
        :param value: value to search for
        :return:
        """
        tracking_code_uuid = str(value)
        try:
            customer_code = int(value)
        except ValueError:
            customer_code = value
        query_object = query_object.filter(
            Q(customer__customer_code__icontains=customer_code) |
            Q(customer__subscriptions__subscription_code__icontains=value) |
            Q(customer__subscriptions__number__icontains=value) |
            Q(tracking_code__icontains=tracking_code_uuid)
        ).distinct()

        return query_object

    @classmethod
    def _filter_from_date_to(cls, query_object, value):
        try:
            from_date_to = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                from_date__lte=from_date_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.FROM_DATE_TO:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_to_date_from(cls, query_object, value):
        try:
            to_date_from = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                to_date__gte=to_date_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.TO_DATE_FROM:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_to_date_to(cls, query_object, value):
        try:
            to_date_to = datetime.fromtimestamp(
                float(value)
            )
            query_object = query_object.filter(
                to_date__lte=to_date_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    FinanceConfigurations.QueryParams.TO_DATE_TO:
                        ErrorMessages.DATE_TIME_400
                }
            )

        return query_object

    @classmethod
    def _filter_invoice_type_code(cls, query_object, value):
        valid_invoice_types = []
        for typ in FinanceConfigurations.Invoice.TYPES:
            valid_invoice_types.append(typ[0])
        invoice_type_query = [
            x.strip() for x in value.split(',')
        ]
        if all(elem in valid_invoice_types
               for elem in invoice_type_query):
            query_object = query_object.filter(
                invoice_type_code__in=invoice_type_query
            )
        else:
            valid_invoice_types = '/'.join(valid_invoice_types)
            error_message = ErrorMessages.VALID_CHOICES_400
            raise api_exceptions.ValidationError400(
                {
                    FinanceConfigurations.QueryParams.INVOICE_TYPE_CODE:
                        f"{error_message}: {valid_invoice_types}"
                }
            )

        return query_object

    @classmethod
    def _filter_base_invoice_status_code(cls, query_object, value):
        valid_status_codes = []
        for sts in FinanceConfigurations.Invoice.STATE_CHOICES:
            valid_status_codes.append(sts[0])
        status_code_query = [
            x.strip() for x in value.split(',')
        ]
        if all(elem in valid_status_codes
               for elem in status_code_query):
            query_object = query_object.filter(
                status_code__in=status_code_query
            )
        else:
            valid_status_codes = '/'.join(
                valid_status_codes,
            )
            raise api_exceptions.ValidationError400(
                {
                    FinanceConfigurations.QueryParams.STATUS_CODE:
                        f"{ErrorMessages.VALID_CHOICES_400}: "
                        f"{valid_status_codes}"
                }
            )

        return query_object

    @classmethod
    def filter_and_order_base_invoice(
            cls,
            model_class_object,
            query_object,
            query_params,
    ):
        """
        Do a common, specific and order by for models classed extended from
        BaseInvoice.
        :param model_class_object: A django model class from BaseInvoice
        :type model_class_object: class
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        query_object = cls.filter_query_common(
            query_object,
            query_params,
        )
        if model_class_object == CreditInvoice:
            query_object = cls.filter_query_credit_invoice(
                query_object,
                query_params,
            )
        elif model_class_object == BaseBalanceInvoice:
            query_object = cls.filter_query_base_balance_invoice(
                query_object,
                query_params,
            )
        else:
            query_object = cls.filter_query_base_invoice(
                query_object,
                query_params,
            )

        if model_class_object == Invoice:
            query_object = cls.filter_query_invoice(
                query_object,
                query_params,
            )

        # Order by based on model's class
        query_object = cls.order_by_query(
            model_class_object,
            query_object,
            query_params,
        )

        return query_object

    @classmethod
    def filter_and_order_payment(cls, query_payment, query_params):
        if FinanceConfigurations.QueryParams.GENERIC_OR in query_params:
            generic_or = query_params[
                FinanceConfigurations.QueryParams.GENERIC_OR
            ]
            used_for_ids = list(
                BaseBalanceInvoice.objects.filter(
                    Q(
                        tracking_code__icontains=generic_or,
                    ) |
                    Q(
                        subscription__number__icontains=generic_or,
                    ) |
                    Q(
                        subscription__subscription_code__icontains=generic_or,
                    )
                ).distinct().values_list('id', flat=True)
            ) + list(
                PackageInvoice.objects.filter(
                    Q(
                        tracking_code__icontains=generic_or,
                    ) |
                    Q(
                        subscription__number__icontains=generic_or,
                    ) |
                    Q(
                        subscription__subscription_code__icontains=generic_or,
                    )).distinct().values_list('id', flat=True)
            ) + list(
                Invoice.objects.filter(
                    Q(
                        tracking_code__icontains=generic_or,
                    ) |
                    Q(
                        subscription__number__icontains=generic_or,
                    ) |
                    Q(
                        subscription__subscription_code__icontains=generic_or,
                    )).distinct().values_list('id', flat=True)
            )
            try:
                customer_code = int(generic_or)
            except ValueError:
                customer_code = 0
            query_payment = query_payment.filter(
                Q(
                    credit_invoice__used_for_id__in
                    =used_for_ids
                ) |
                Q(
                    credit_invoice__customer__customer_code__icontains
                    =customer_code
                ) |
                Q(
                    credit_invoice__tracking_code__icontains=
                    generic_or
                ) |
                Q(
                    id__icontains=generic_or
                )
            ).distinct()

        if FinanceConfigurations.QueryParams.ID in query_params:
            query_payment = query_payment.filter(
                id__icontains=query_params[
                    FinanceConfigurations.QueryParams.ID
                ],
            ).distinct()

        if FinanceConfigurations.QueryParams.PRIME_CODE in query_params:
            try:
                customer_code = int(
                    query_params[
                        FinanceConfigurations.QueryParams.PRIME_CODE
                    ])
            except ValueError:
                customer_code = 0
            query_payment = query_payment.filter(
                credit_invoice__customer__customer_code__icontains=
                customer_code,
            ).distinct()

        if FinanceConfigurations.QueryParams.TRACKING_CODE in query_params:
            query_payment = query_payment.filter(
                credit_invoice__tracking_code__icontains=
                query_params[
                    FinanceConfigurations.QueryParams.TRACKING_CODE
                ],
            ).distinct()

        if FinanceConfigurations.QueryParams.SUBSCRIPTION_CODE in query_params:
            query = query_params[
                FinanceConfigurations.QueryParams.SUBSCRIPTION_CODE
            ]
            used_for_ids = list(
                BaseBalanceInvoice.objects.filter(
                    subscription__subscription_code__icontains=query,
                ).values_list('id', flat=True)
            ) + list(
                PackageInvoice.objects.filter(
                    subscription__subscription_code__icontains=query,
                ).values_list('id', flat=True)
            ) + list(
                Invoice.objects.filter(
                    subscription__subscription_code__icontains=query,
                ).values_list('id', flat=True)
            )
            query_payment = query_payment.filter(
                credit_invoice__used_for_id__in=used_for_ids
            ).distinct()

        if FinanceConfigurations.QueryParams.NUMBER in query_params:
            query = query_params[
                FinanceConfigurations.QueryParams.NUMBER
            ]
            used_for_ids = list(
                BaseBalanceInvoice.objects.filter(
                    subscription__number__icontains=query,
                ).values_list('id', flat=True)
            ) + list(
                PackageInvoice.objects.filter(
                    subscription__number__icontains=query,
                ).values_list('id', flat=True)
            ) + list(
                Invoice.objects.filter(
                    subscription__number__icontains=query,
                ).values_list('id', flat=True)
            )
            query_payment = query_payment.filter(
                credit_invoice__used_for_id__in=used_for_ids
            ).distinct()

        if FinanceConfigurations.QueryParams.GATEWAY in query_params:
            query_payment = query_payment.filter(
                gateway=query_params[
                    FinanceConfigurations.QueryParams.GATEWAY
                ],
            )

        if FinanceConfigurations.QueryParams.CREATED_AT_FROM in query_params:
            query_payment = cls._filter_created_at_from(
                query_payment,
                query_params[FinanceConfigurations.QueryParams.CREATED_AT_FROM]
            )

        if FinanceConfigurations.QueryParams.CREATED_AT_TO in query_params:
            query_payment = cls._filter_created_at_to(
                query_payment,
                query_params[FinanceConfigurations.QueryParams.CREATED_AT_TO]
            )

        if FinanceConfigurations.QueryParams.STATUS_CODE in query_params:
            valid_status_codes = []
            for sts in FinanceConfigurations.Payment.STATE_CHOICES:
                valid_status_codes.append(sts[0])
            status_code_query = [
                x.strip() for x in query_params
                [FinanceConfigurations.QueryParams.STATUS_CODE].split(',')
            ]
            if all(elem in valid_status_codes
                   for elem in status_code_query):
                query_payment = query_payment.filter(
                    status_code__in=status_code_query
                )
            else:
                valid_status_codes = '/'.join(
                    valid_status_codes,
                )
                error_message = ErrorMessages.VALID_CHOICES_400
                raise api_exceptions.ValidationError400(
                    {
                        FinanceConfigurations.QueryParams.STATUS_CODE:
                            f"{error_message}: {valid_status_codes}"
                    }
                )

        query_payment = CommonService.order_by_query(
            Payment,
            query_payment,
            query_params,
        )

        return query_payment

    @classmethod
    def filter_from_and_to_date(cls, query_object, query_params):
        """
        Filters on from_date and to_date in a model's class
        :param query_object: A django ORM query
        :type query_object: object
        :param query_params: A dict of query params
        :type query_params: dict
        :return: A django ORM query
        :rtype: object
        """
        if FinanceConfigurations.QueryParams.FROM_DATE_FROM in query_params:
            query_object = cls._filter_from_date_from(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.FROM_DATE_FROM
                ]
            )

        if FinanceConfigurations.QueryParams.FROM_DATE_TO in query_params:
            query_object = cls._filter_from_date_to(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.FROM_DATE_TO
                ]
            )

        if FinanceConfigurations.QueryParams.TO_DATE_FROM in query_params:
            query_object = cls._filter_to_date_from(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.TO_DATE_FROM
                ]
            )

        if FinanceConfigurations.QueryParams.TO_DATE_TO in query_params:
            query_object = cls._filter_to_date_from(
                query_object,
                query_params[
                    FinanceConfigurations.QueryParams.TO_DATE_TO
                ]
            )

        return query_object

    @classmethod
    def get_expired_at(cls, package_due):
        """
        Convert due date (FinanceConfigurations.Package.TYPES) to datetime
        object. This is useful for prepaid balances' expiry date
        :param package_due: FinanceConfigurations.Package.TYPES
        :return:
        """
        today = datetime.now()
        if package_due == FinanceConfigurations.Package.TYPES[0][0]:
            return today + timedelta(days=1)
        elif package_due == FinanceConfigurations.Package.TYPES[1][0]:
            return today + timedelta(days=3)
        elif package_due == FinanceConfigurations.Package.TYPES[2][0]:
            return today + timedelta(days=5)
        elif package_due == FinanceConfigurations.Package.TYPES[3][0]:
            return today + timedelta(days=7)
        elif package_due == FinanceConfigurations.Package.TYPES[4][0]:
            return today + timedelta(days=15)
        elif package_due == FinanceConfigurations.Package.TYPES[5][0]:
            return today + timedelta(days=30)
        elif package_due == FinanceConfigurations.Package.TYPES[6][0]:
            return today + timedelta(days=45)
        elif package_due == FinanceConfigurations.Package.TYPES[7][0]:
            return today + timedelta(days=60)
        elif package_due == FinanceConfigurations.Package.TYPES[8][0]:
            return today + timedelta(days=90)
        elif package_due == FinanceConfigurations.Package.TYPES[9][0]:
            return today + timedelta(days=120)
        elif package_due == FinanceConfigurations.Package.TYPES[10][0]:
            return today + timedelta(days=180)
        elif package_due == FinanceConfigurations.Package.TYPES[11][0]:
            return today + timedelta(days=365)

    @classmethod
    def get_subscription_object(cls, customer_code, subscription_code):
        """
        Return subscription object based on customer and subscription code
        :param customer_code:
        :param subscription_code:
        :return:
        """
        if subscription_code is None:
            raise api_exceptions.ValidationError400(
                {
                    "subscription_code": _("Subscription id is not provided")
                }
            )
        if customer_code is not None:
            try:
                subscription_object = Subscription.objects.get(
                    customer__customer_code=customer_code,
                    subscription_code=subscription_code,
                    is_allocated=True,
                )
            except Subscription.DoesNotExist:
                error_message = _(
                    'Subscription does not belongs to this customer or is '
                    'not allocated'
                )
                raise api_exceptions.NotFound404(
                    f"{error_message}: "
                    f"{subscription_code}"
                )
        else:
            try:
                subscription_object = Subscription.objects.get(
                    subscription_code=subscription_code,
                    is_allocated=True,
                )
            except Subscription.DoesNotExist:
                error_message = _(
                    'Subscription does not exists or is not allocated',
                )
                raise api_exceptions.NotFound404(
                    f"{error_message}: "
                    f"{subscription_code}"
                )

        return subscription_object

    @classmethod
    def base_invoice_conditions(
            cls,
            customer_code=None,
            subscription_code=None,
    ):
        """
        Generate conditions based on BaseInvoice (Use this in Invoice,
        PackageInvoice, BaseBalanceInvoice)
        :param customer_code:
        :param subscription_code:
        :return:
        """
        conditions = {}
        if customer_code:
            conditions.update(
                {
                    "subscription__customer__customer_code": customer_code,
                }
            )
        if subscription_code:
            conditions.update(
                {
                    "subscription__subscription_code": subscription_code,
                }
            )

        return conditions

    @classmethod
    def credit_invoice_conditions(
            cls,
            customer_code=None,
            subscription_code=None,
    ):
        """
        Generate conditions based on CreditInvoice
        :param customer_code:
        :param subscription_code:
        :return:
        """
        conditions = {}
        if customer_code:
            conditions.update(
                {
                    "customer__customer_code": customer_code,
                }
            )
        if subscription_code:
            conditions.update(
                {
                    "customer__subscriptions__subscription_code":
                        subscription_code,
                }
            )

        return conditions

    @classmethod
    def payment_conditions(
            cls,
            customer_code=None,
            subscription_code=None,
            credit_invoice_id=None,
    ):
        """
        Generate conditions based on CreditInvoice
        :param credit_invoice_id:
        :param customer_code:
        :param subscription_code:
        :return:
        """
        conditions = {}
        if credit_invoice_id:
            conditions.update(
                {
                    "credit_invoice__id": credit_invoice_id,
                }
            )
        if customer_code:
            conditions.update(
                {
                    "credit_invoice__customer__customer_code": customer_code,
                }
            )
        if subscription_code:
            conditions.update(
                {
                    "credit_invoice__customer__subscriptions__subscription_code":
                        subscription_code,
                }
            )

        return conditions

    @classmethod
    def payment_cool_time(cls):
        """
        Return payment cool down from datetime.now() based on
        FinanceConfigurations.RuntimeConfig.KEY_CHOICES
        """
        cool_minutes = int(
            RuntimeConfigService.get_value(
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[8][0]
            )
        )

        return datetime.now() + timedelta(minutes=cool_minutes)
