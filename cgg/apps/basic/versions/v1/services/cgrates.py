# --------------------------------------------------------------------------
# Logic based methods used in basic app's public API.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - cgrates.py
# Created at 2020-8-29,  16:33:56
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions,
)
from cgg.apps.basic.versions.v1.serializers.cgrates import (
    AccountSerializer,
    RemoveRatingProfileSerializer,
    ReverseDestinationRateSerializer,
    ReverseRateSerializer,
    ReverseRatingPlanSerializer,
    ReverseRatingProfileSerializer,
    ReverseTimingSerializer,
)
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.core import api_exceptions
from cgg.core.tools import Tools


class CGRateSService:

    @classmethod
    def get_accounts(
            cls,
            query_params,
            limit,
            offset,
    ):
        account_ids = []

        if 'account_ids' in query_params:
            account_ids = [
                CGRatesConventions.account_name_no_tenant(
                    e.strip())
                for e in query_params['account_ids'].split(',')
            ]

        accounts_objects = BasicService.get_accounts(
            account_ids=account_ids,
            limit=limit,
            offset=offset,
        )
        accounts_objects_serializer = AccountSerializer(
            data=accounts_objects,
            many=True,
        )

        if not accounts_objects_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                accounts_objects_serializer.errors
            )

        return accounts_objects_serializer.data

    @classmethod
    def get_account(cls, account):
        subscription_code = \
            CGRatesConventions.revert_account_name(
                original_name=account,
                with_tenant=False,
            )
        account_object = BasicService.get_account(
            subscription_code
        )
        account_object_serializer = AccountSerializer(
            data=account_object,
        )

        if not account_object_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                account_object_serializer.errors
            )

        return account_object_serializer.data

    @classmethod
    def get_cdrs_count(
            cls,
            query_params,
    ):
        subscription_codes = []
        setup_time_start = None
        setup_time_end = None
        created_at_start = None
        created_at_end = None
        destination_prefixes = []
        not_destination_prefixes = []

        if 'account_ids' in query_params:
            subscription_codes = [
                CGRatesConventions.revert_account_name(
                    original_name=e.strip(),
                    with_tenant=True,
                ) for e in query_params['account_ids'].split(',')
            ]

        if 'destination_prefixes' in query_params:
            destination_prefixes = [
                e.strip() for e in
                query_params['destination_prefixes'].split(',')
            ]

        if 'not_destination_prefixes' in query_params:
            not_destination_prefixes = [
                e.strip() for e in
                query_params['not_destination_prefixes'].split(',')
            ]

        if 'setup_time_start' in query_params:
            setup_time_start = query_params['setup_time_start']

        if 'setup_time_end' in query_params:
            setup_time_end = query_params['setup_time_end']

        if 'created_at_start' in query_params:
            created_at_start = query_params['created_at_start']

        if 'created_at_end' in query_params:
            created_at_end = query_params['created_at_end']

        cdrs_count = BasicService.get_cdrs_count(
            subscription_codes=subscription_codes,
            setup_time_start=setup_time_start,
            setup_time_end=setup_time_end,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
            destination_prefixes=destination_prefixes,
            not_destination_prefixes=not_destination_prefixes,
        )

        return cdrs_count

    @classmethod
    def get_cdrs(
            cls,
            query_params,
            limit,
            offset,
    ):
        subscription_codes = []
        setup_time_start = None
        setup_time_end = None
        created_at_start = None
        created_at_end = None
        destination_prefixes = []
        not_destination_prefixes = []

        if 'account_ids' in query_params:
            subscription_codes = [
                CGRatesConventions.revert_account_name(
                    original_name=e.strip(),
                    with_tenant=True,
                ) for e in query_params['account_ids'].split(',')
            ]

        if 'destination_prefixes' in query_params:
            destination_prefixes = [
                e.strip() for e in
                query_params['destination_prefixes'].split(',')
            ]

        if 'not_destination_prefixes' in query_params:
            not_destination_prefixes = [
                e.strip() for e in
                query_params['not_destination_prefixes'].split(',')
            ]

        if 'setup_time_start' in query_params:
            setup_time_start = query_params['setup_time_start']

        if 'setup_time_end' in query_params:
            setup_time_end = query_params['setup_time_end']

        if 'created_at_start' in query_params:
            created_at_start = query_params['created_at_start']

        if 'created_at_end' in query_params:
            created_at_end = query_params['created_at_end']

        cdr_from_cgrates = BasicService.get_cdrs(
            subscription_codes=subscription_codes,
            setup_time_start=setup_time_start,
            setup_time_end=setup_time_end,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
            destination_prefixes=destination_prefixes,
            not_destination_prefixes=not_destination_prefixes,
            limit=limit,
            offset=offset,
        )

        cdr_objects = BasicService.cdrs_object(
            cdr_from_cgrates,
        )

        return cdr_objects

    @classmethod
    def get_actions(
            cls,
            query_params,
            limit,
            offset,
    ):
        action_ids = []
        if 'action_ids' in query_params:
            action_ids = [
                e.strip() for e in query_params['action_ids'].split(',')
            ]

        actions_objects = BasicService.get_actions(
            action_ids,
            limit,
            offset,
        )

        return actions_objects

    @classmethod
    def get_attributes(
            cls,
            limit,
            offset,
    ):
        attributes_objects = BasicService.get_attributes(
            limit,
            offset,
        )

        if attributes_objects is not None:
            return [
                {'id': identifier} for identifier in attributes_objects
            ]

        return []

    @classmethod
    def get_attribute(
            cls,
            attribute,

    ):
        attribute_object = BasicService.get_attribute(
            attribute,
        )

        return attribute_object

    @classmethod
    def get_destinations(cls, query_params):
        destination_ids = []
        if 'destination_ids' in query_params:
            destination_ids = [
                e.strip() for e in query_params['destination_ids'].split(',')
            ]
        try:
            destinations_object = BasicService.get_destinations(
                destination_ids,
            )
        except api_exceptions.NotFound404:
            destinations_object = []

        return destinations_object

    @classmethod
    def get_threshold(cls, threshold):
        threshold_object = BasicService.get_threshold(
            threshold,
        )

        return threshold_object

    @classmethod
    def get_thresholds(cls, query_params, limit, offset):
        thresholds_object = BasicService.get_thresholds(
            limit,
            offset,
        )

        if thresholds_object is not None:
            return [
                {'id': identifier} for identifier in thresholds_object
            ]

        return []

    @classmethod
    def get_filter(cls, filter_name):
        filter_object = BasicService.get_filter(
            filter_name,
        )

        return filter_object

    @classmethod
    def get_filters(cls, query_params, limit, offset):

        filters_object = BasicService.get_filters(
            limit,
            offset,
        )

        if filters_object is not None:
            return [
                {'id': identifier} for identifier in filters_object
            ]

        return []

    @classmethod
    def get_suppliers(cls, query_params, limit, offset):
        suppliers_object = BasicService.get_suppliers(
            limit,
            offset,
        )

        if suppliers_object is not None:
            return [
                {'id': identifier} for identifier in suppliers_object
            ]

        return []

    @classmethod
    def get_supplier(cls, supplier):
        supplier_object = BasicService.get_supplier(
            supplier,
        )

        return supplier_object

    @classmethod
    def get_charger(cls, charger):
        charger_object = BasicService.get_charger_profile(
            charger,
        )

        return charger_object

    @classmethod
    def get_chargers(cls, query_params, limit, offset):
        chargers_object = BasicService.get_chargers(
            limit,
            offset,
        )

        if chargers_object is not None:
            return [
                {'id': identifier} for identifier in chargers_object
            ]

        return []

    @classmethod
    def get_rate(cls, rate):
        rate_object = BasicService.get_rate(
            rate,
        )

        return rate_object

    @classmethod
    def get_rates(cls, query_params, limit, offset):
        rates_object = BasicService.get_rates(
            limit,
            offset,
        )

        if rates_object is not None:
            return [
                {'id': identifier} for identifier in rates_object
            ]

        return []

    @classmethod
    def get_destination_rate(cls, destination_rate):
        destination_rate_object = BasicService.get_destination_rate(
            destination_rate,
        )

        return destination_rate_object

    @classmethod
    def get_destination_rates(cls, query_params, limit, offset):
        destination_rates_object = BasicService.get_destination_rates(
            limit,
            offset,
        )

        if destination_rates_object is not None:
            return [
                {'id': identifier} for identifier in destination_rates_object
            ]

        return []

    @classmethod
    def get_timings(cls, query_params, limit, offset):
        timings_object = BasicService.get_timings(
            limit,
            offset,
        )

        if timings_object is not None:
            return [
                {'id': identifier} for identifier in timings_object
            ]

        return []

    @classmethod
    def get_timing(cls, timing):
        timing_object = BasicService.get_timing(
            timing,
        )

        return timing_object

    @classmethod
    def get_rating_plan(cls, rating_plan):
        rating_plan_object = BasicService.get_rating_plan(
            rating_plan,
        )

        return rating_plan_object

    @classmethod
    def get_rating_plans(cls, query_params, limit, offset):
        rating_plans_object = BasicService.get_rating_plans(
            limit,
            offset,
        )

        if rating_plans_object is not None:
            return [
                {'id': identifier} for identifier in rating_plans_object
            ]

        return []

    @classmethod
    def get_rating_profiles(cls, query_params, limit, offset):
        rating_profiles_object = BasicService.get_rating_profiles(
            limit,
            offset,
        )

        if rating_profiles_object is not None:
            return [
                {'id': identifier} for identifier in rating_profiles_object
            ]

        return []

    @classmethod
    def get_rating_profile(cls, rating_profile):
        rating_profile_object = BasicService.get_rating_profile(
            rating_profile,
        )

        return rating_profile_object

    @classmethod
    def add_rate(cls, body):
        body = Tools.get_dict_from_json(body)
        rate_serializer = ReverseRateSerializer(
            data=body
        )

        if rate_serializer.is_valid(raise_exception=True):
            rate_body = rate_serializer.data

            return BasicService.set_rate(rate_body)

    @classmethod
    def add_destination_rates(cls, body):
        body = Tools.get_dict_from_json(body)
        destination_rate_serializer = ReverseDestinationRateSerializer(
            data=body
        )

        if destination_rate_serializer.is_valid(raise_exception=True):
            destination_rate_body = destination_rate_serializer.data

            return BasicService.set_destination_rate(
                destination_rate_body,
            )

    @classmethod
    def add_timings(cls, body):
        body = Tools.get_dict_from_json(body)
        timings_serializer = ReverseTimingSerializer(
            data=body
        )

        if timings_serializer.is_valid(raise_exception=True):
            timings_body = timings_serializer.data

            return BasicService.set_timings(
                timings_body,
            )

    @classmethod
    def add_rating_plans(cls, body):
        body = Tools.get_dict_from_json(body)
        rating_plans_serializer = ReverseRatingPlanSerializer(
            data=body
        )

        if rating_plans_serializer.is_valid(raise_exception=True):
            rating_plans_body = rating_plans_serializer.data

            return BasicService.set_rating_plan(rating_plans_body)

    @classmethod
    def add_rating_profile(cls, body):
        body = Tools.get_dict_from_json(body)
        rating_profile_serializer = ReverseRatingProfileSerializer(
            data=body
        )

        if rating_profile_serializer.is_valid(raise_exception=True):
            return BasicService.set_rating_profile(
                rating_profile_serializer.data,
            )

    @classmethod
    def remove_rate(cls, rate):
        return BasicService.remove_rate(rate)

    @classmethod
    def remove_destination_rate(cls, destination_rate):
        return BasicService.remove_destination_rate(destination_rate)

    @classmethod
    def delete_timing(cls, timing):
        return BasicService.remove_timing(timing)

    @classmethod
    def remove_rating_plan(cls, rating_plan):
        return BasicService.remove_rating_plan(rating_plan)

    @classmethod
    def remove_rating_profile(cls, rating_profile, body):
        body = Tools.get_dict_from_json(body)
        rating_profile_serializer = RemoveRatingProfileSerializer(
            data=body
        )

        if rating_profile_serializer.is_valid(raise_exception=True):
            return BasicService.remove_rating_profile(
                rating_profile,
                rating_profile_serializer.data['category'],
                rating_profile_serializer.data['subject'],
            )

    @classmethod
    def reload_plans(cls):
        return BasicService.load_tariff_plan()
