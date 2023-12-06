# --------------------------------------------------------------------------
# CGRateS values must match the conventions defined here:
# https://godoc.org/github.com/cgrates/cgrates/apier/v1
# https://godoc.org/github.com/cgrates/cgrates/apier/v2
# (C) 2019 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - api.py
# Created at 2019-12-9,  15:58:7
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
from rest_framework import exceptions
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from cgg.apps.basic.apps import BasicConfig
from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.apps.basic.versions.v1.services.cgrates import (
    CGRateSService,
)



from cgg.core.decorators import log_api_request
from cgg.core.paginator import Paginator
from cgg.core.permissions import (
    DashboardAPIPermission,
    TrunkBackendAPIPermission,
)
from cgg.core.response import response



from cgg.apps.finance.versions.v1.services.invoice import (
    InvoiceService,
)

from cgg.apps.finance.models import (
    Subscription,
)



def make_cgrates_paginate(request, count=10):
    # TODO: Get count of all objects from CGRateS
    limit = api_settings.PAGE_SIZE
    offset = 0

    if 'limit' in request.query_params:
        limit = int(request.query_params['limit'])

    if 'offset' in request.query_params:
        offset = int(request.query_params['offset'])

    pagination = Paginator()
    pagination.offset = offset
    pagination.limit = limit
    pagination.count = count
    pagination.request = request

    return {
        'pagination': pagination,
        'limit': limit,
        'offset': offset
    }


class AccountsAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_ACCOUNTS,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_accounts(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of all accounts'),
        )


class AccountAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_ACCOUNT,
    )
    def get(
            self,
            request,
            account,
            *args,
            **kwargs,
    ):
        try:
            data = CGRateSService.get_account(account)
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=data,
            message=_('Details of an account'),
        )


class CDRsAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_CDRS,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cdrs_count = CGRateSService.get_cdrs_count(
                request.query_params,
            )
            cgrates_pagination = make_cgrates_paginate(request, cdrs_count)
            response_data = CGRateSService.get_cdrs(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of CDRs'),
        )


class ActionsAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_ACTIONS,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_actions(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of actions'),
        )


class AttributesAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_ATTRIBUTES,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_attributes(
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of attributes'),
        )


class AttributeAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_ATTRIBUTE,
    )
    def get(
            self,
            request,
            attribute,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_attribute(
                attribute
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of an attribute'),
        )


class DestinationsAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_DESTINATIONS,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_destinations(
                request.query_params,
            )
            cgrates_pagination = make_cgrates_paginate(
                request,
                len(response_data),
            )

        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of destinations'),
        )


class ThresholdsAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_THRESHOLDS,
    )
    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_thresholds(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of thresholds'),
        )


class ThresholdAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_THRESHOLD,
    )
    def get(
            self,
            request,
            threshold,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_threshold(
                threshold
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a threshold'),
        )


class FiltersAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_FILTERS,
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_filters(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of filters'),
        )


class FilterAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_FILTER,
    )
    def get(
            self,
            request,
            filter_name,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_filter(
                filter_name
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a filter'),
        )


class SuppliersAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_SUPPLIERS
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_suppliers(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of suppliers'),
        )


class SupplierAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_SUPPLIER,
    )
    def get(
            self,
            request,
            supplier,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_supplier(
                supplier
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a supplier'),
        )


class ChargersAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_CHARGERS
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_chargers(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of chargers'),
        )


class ChargerAPIView(APIView):
    permission_classes = (DashboardAPIPermission,)

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_CHARGER,
    )
    def get(
            self,
            request,
            charger,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_charger(
                charger
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a charger'),
        )


class RatesAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATES
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_rates(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of rates'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.ADD_RATE
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.add_rate(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('A new rate is created successfully'),
        )


class RateAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATE
    )
    def get(
            self,
            request,
            rate,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_rate(
                rate
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a rate'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.DELETE_RATE
    )
    def delete(
            self,
            request,
            rate,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.remove_rate(
                rate
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Rate is removed successfully'),
        )


class DestinationRatesAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_DESTINATION_RATES
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_destination_rates(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of destination rates'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.ADD_DESTINATION_RATES
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.add_destination_rates(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('A new destination rate is created successfully'),
        )


class DestinationRateAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_DESTINATION_RATE
    )
    def get(
            self,
            request,
            destination_rate,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_destination_rate(
                destination_rate
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of destination rate'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.REMOVE_DESTINATION_RATE
    )
    def delete(
            self,
            request,
            destination_rate,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.remove_destination_rate(
                destination_rate
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Destination rate is removed successfully'),
        )


class TimingsAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_TIMINGS
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_timings(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of timings'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.SET_TIMINGS
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.add_timings(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('A new timing is created successfully'),
        )


class TimingAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_TIMING
    )
    def get(
            self,
            request,
            timing,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_timing(
                timing
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a timing'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.DELETE_TIMING
    )
    def delete(
            self,
            request,
            timing,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.delete_timing(
                timing
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Timing is removed successfully'),
        )


class RatingPlanAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATING_PLAN
    )
    def get(
            self,
            request,
            rating_plan,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.get_rating_plan(
                rating_plan
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a rating plan'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.REMOVE_RATING_PLAN
    )
    def delete(
            self,
            request,
            rating_plan,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.remove_rating_plan(
                rating_plan
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Rating plan is removed successfully'),
        )


class RatingPlansAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATING_PLANS
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_rating_plans(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of rating plans'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.SET_RATING_PLANS
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.add_rating_plans(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('A new rating plan is created successfully'),
        )


class RatingProfilesAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATING_PROFILES
    )
    def get(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_rating_profiles(
                request.query_params,
                cgrates_pagination['limit'],
                cgrates_pagination['offset']
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of rating profiles'),
        )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATING_PROFILES
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.add_rating_profile(
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('A new rating profile is created successfully'),
        )


class RatingProfileAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @method_decorator(
        cache_page(settings.CGG['CACHE_EXPIRY_GLOBAL']),
    )
    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.GET_RATING_PROFILE
    )
    def get(
            self,
            request,
            rating_profile,
            *args,
            **kwargs,
    ):
        try:
            # Rating profiles by load id are a list of objects
            cgrates_pagination = make_cgrates_paginate(request)
            response_data = CGRateSService.get_rating_profile(
                rating_profile
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_data = (response_data, cgrates_pagination['pagination'])

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Details of a rating profile'),
        )


class RatingProfileDeleteAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission | TrunkBackendAPIPermission,
    )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.DELETE_RATING_PROFILE
    )
    def post(
            self,
            request,
            rating_profile,
            *args,
            **kwargs,
    ):
        try:
            # body must contain subject and category
            response_data = CGRateSService.remove_rating_profile(
                rating_profile,
                request.body,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Rating profile is removed successfully'),
        )


class ReloadPlansAPIView(APIView):
    permission_classes = (
        DashboardAPIPermission,
    )

    @log_api_request(
        app_name=BasicConfig.name,
        label=BasicConfigurations.APIRequestLabels.RELOAD_PLANS
    )
    def post(
            self,
            request,
            *args,
            **kwargs,
    ):
        try:
            response_data = CGRateSService.reload_plans()
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=200,
            data=response_data,
            message=_('Tariff plans reloaded successfully'),
        )


class TestAPIView(APIView):
    
    def get(
        self,
        request,
        *args,
        **kwargs,
    ):


        subscription_id = ""
        subscription_object = Subscription.objects.get(
                id=subscription_id,
                is_allocated=True,
            )

        from_date = ""
        to_date   = ""

        invoice_type_code = invoice_config.TYPES[0][0]
        description = ""

        invoice_object, payed = InvoiceService.issue_invoice(subscription_object, from_date, to_date, invoice_type_code, description)


        return response(
            request,
            status=200,
            data= invoice_object,
            message=_('Testing'),
        )
  