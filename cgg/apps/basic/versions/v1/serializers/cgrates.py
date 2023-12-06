# --------------------------------------------------------------------------
# If a serializer needs to be updated, check for Reverse of that serializer
# and update that as well.
# (C) 2019 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - cgrates.py
# Created at 2019-12-9,  15:2:41
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------


from rest_framework import serializers

from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions,
)
from cgg.core.tools import Tools


class RemoveRatingProfileSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    subject = serializers.CharField(required=True)
    category = serializers.CharField(required=True)


class ReverseRatingPlanActivationSerializer(serializers.Serializer):
    activation_time = serializers.CharField(required=True)
    rating_plan_id = serializers.CharField(required=True)
    fallback_subjects = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'ActivationTime': instance['activation_time'],
            'RatingPlanId': instance['rating_plan_id'],
            'FallbackSubjects': instance['fallback_subjects'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseRatingProfileSerializer(serializers.Serializer):
    category = serializers.CharField(required=True)
    subject = serializers.CharField(required=True)
    rating_plan_activations = ReverseRatingPlanActivationSerializer(
        required=True,
        many=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)
        rating_plan_activations = ReverseRatingPlanActivationSerializer(
            data=instance['rating_plan_activations'],
            many=True,
        )

        if rating_plan_activations.is_valid(raise_exception=True):
            rating_plan_activations = rating_plan_activations.data

        return {
            'Category': instance['category'],
            'Subject': instance['subject'],
            'RatingPlanActivations': rating_plan_activations,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RatingPlanActivationSerializer(serializers.Serializer):
    ActivationTime = serializers.CharField(required=True)
    RatingPlanId = serializers.CharField(required=True)
    FallbackSubjects = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'activation_time': instance['ActivationTime'],
            'rating_plan_id': instance['RatingPlanId'],
            'fallback_subjects': instance['FallbackSubjects'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RatingProfileSerializer(serializers.Serializer):
    TPid = serializers.CharField(required=True)
    LoadId = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    Category = serializers.CharField(required=True)
    Subject = serializers.CharField(required=True)
    RatingPlanActivations = RatingPlanActivationSerializer(
        required=True,
        many=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)
        rating_plan_activations = RatingPlanActivationSerializer(
            data=instance['RatingPlanActivations'],
            many=True,
        )

        if rating_plan_activations.is_valid(raise_exception=True):
            rating_plan_activations = rating_plan_activations.data

        return {
            'id': instance['TPid'],
            'load_id': instance['LoadId'],
            'tenant': instance['Tenant'],
            'category': instance['Category'],
            'subject': instance['Subject'],
            'rating_plan_activations': rating_plan_activations,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RatingPlanBindingsSerializer(serializers.Serializer):
    DestinationRatesId = serializers.CharField(required=True)
    TimingId = serializers.CharField(required=True)
    Weight = serializers.IntegerField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'destination_rates_id': instance['DestinationRatesId'],
            'timing_id': instance['TimingId'],
            'weight': instance['Weight'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RatingPlanSerializer(serializers.Serializer):
    TPid = serializers.CharField(required=True)
    ID = serializers.CharField(required=True)
    RatingPlanBindings = RatingPlanBindingsSerializer(
        required=True,
        many=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)

        rating_plan_bindings = RatingPlanBindingsSerializer(
            data=instance['RatingPlanBindings'],
            many=True,
        )

        if rating_plan_bindings.is_valid(raise_exception=True):
            rating_plan_bindings = rating_plan_bindings.data

        return {
            'tariff_plan_id': instance['TPid'],
            'id': instance['ID'],
            'rating_plan_bindings': rating_plan_bindings,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseRatingPlanBindingsSerializer(serializers.Serializer):
    destination_rates_id = serializers.CharField(required=True)
    timing_id = serializers.CharField(required=True)
    weight = serializers.IntegerField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'DestinationRatesId': instance['destination_rates_id'],
            'TimingId': instance['timing_id'],
            'Weight': instance['weight'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseRatingPlanSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    rating_plan_bindings = ReverseRatingPlanBindingsSerializer(
        required=True,
        many=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)

        rating_plan_bindings = ReverseRatingPlanBindingsSerializer(
            data=instance['rating_plan_bindings'],
            many=True,
        )

        if rating_plan_bindings.is_valid(raise_exception=True):
            rating_plan_bindings = rating_plan_bindings.data

        return {
            'ID': CGRatesConventions.rating_plan(instance['id']),
            'RatingPlanBindings': rating_plan_bindings,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseTimingSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    years = serializers.CharField(required=True, allow_null=True)
    months = serializers.CharField(required=True, allow_null=True)
    month_days = serializers.CharField(required=True, allow_null=True)
    week_days = serializers.CharField(required=True, allow_null=True)
    time = serializers.CharField(required=True, allow_null=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'ID': CGRatesConventions.timings(instance['id']),
            'Years': instance['years'],
            'Months': instance['months'],
            'MonthDays': instance['month_days'],
            'WeekDays': instance['week_days'],
            'Time': instance['time'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class TimingSerializer(serializers.Serializer):
    TPid = serializers.CharField(required=True)
    ID = serializers.CharField(required=True)
    Years = serializers.CharField(required=True, allow_null=True)
    Months = serializers.CharField(required=True, allow_null=True)
    MonthDays = serializers.CharField(required=True, allow_null=True)
    WeekDays = serializers.CharField(required=True, allow_null=True)
    Time = serializers.CharField(required=True, allow_null=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'tariff_plan_id': instance['TPid'],
            'id': instance['ID'],
            'years': instance['Years'],
            'months': instance['Months'],
            'month_days': instance['MonthDays'],
            'week_days': instance['WeekDays'],
            'time': instance['Time'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RateSlotsSerializer(serializers.Serializer):
    ConnectFee = serializers.IntegerField(required=True)
    Rate = serializers.IntegerField(required=True)
    RateUnit = serializers.CharField(required=True)
    RateIncrement = serializers.CharField(required=True)
    GroupIntervalStart = serializers.CharField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'connect_fee': instance['ConnectFee'],
            'rate': instance['Rate'],
            'rate_unit': instance['RateUnit'],
            'rate_increment': instance['RateIncrement'],
            'group_interval_start': instance['GroupIntervalStart'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RateSerializer(serializers.Serializer):
    TPid = serializers.CharField(required=True)
    ID = serializers.CharField(required=True)
    RateSlots = RateSlotsSerializer(required=True, many=True)

    def to_representation(self, instance):
        instance = dict(instance)
        rate_slots = RateSlotsSerializer(
            data=instance['RateSlots'],
            many=True,
        )

        if rate_slots.is_valid(raise_exception=True):
            rate_slots = rate_slots.data

        return {
            'tariff_plan_id': instance['TPid'],
            'id': instance['ID'],
            'rate_slots': rate_slots,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseRateSlotsSerializer(serializers.Serializer):
    connect_fee = serializers.IntegerField(required=True)
    rate = serializers.IntegerField(required=True)
    rate_unit = serializers.CharField(required=True)
    rate_increment = serializers.CharField(required=True)
    group_interval_start = serializers.CharField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'ConnectFee': instance['connect_fee'],
            'Rate': instance['rate'],
            'RateUnit': instance['rate_unit'],
            'RateIncrement': instance['rate_increment'],
            'GroupIntervalStart': instance['group_interval_start'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseRateSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    rate_slots = ReverseRateSlotsSerializer(required=True, many=True)

    def to_representation(self, instance):
        instance = dict(instance)
        rate_slots = ReverseRateSlotsSerializer(
            data=instance['rate_slots'],
            many=True,
        )

        if rate_slots.is_valid(raise_exception=True):
            rate_slots = rate_slots.data

        return {
            'ID': CGRatesConventions.rate(instance['id']),
            'RateSlots': rate_slots,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DestinationRatesSerializer(serializers.Serializer):
    DestinationId = serializers.CharField(required=True)
    RateId = serializers.CharField(required=True)
    Rate = RateSerializer(required=True, allow_null=True, many=True)
    RoundingMethod = serializers.CharField(required=True)
    RoundingDecimals = serializers.IntegerField(required=True)
    MaxCost = serializers.IntegerField(required=True)
    MaxCostStrategy = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)
        rate = None
        if instance['Rate'] is not None:
            rate = RateSerializer(data=instance['Rate'])

            if rate.is_valid(raise_exception=True):
                rate = rate.data

        return {
            'destination_id': instance['DestinationId'],
            'rate_id': instance['RateId'],
            'rate': rate,
            'rounding_method': instance['RoundingMethod'],
            'rounding_decimals': instance['RoundingDecimals'],
            'max_cost': instance['MaxCost'],
            'max_cost_strategy': instance['MaxCostStrategy'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseDestinationRatesSerializer(serializers.Serializer):
    destination_id = serializers.CharField(required=True)
    rate_id = serializers.CharField(required=True)
    rounding_method = serializers.CharField(required=True)
    rounding_decimals = serializers.IntegerField(required=True)
    max_cost = serializers.IntegerField(required=True)
    max_cost_strategy = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'DestinationId': instance['destination_id'],
            'RateId': instance['rate_id'],
            'RoundingMethod': instance['rounding_method'],
            'RoundingDecimals': instance['rounding_decimals'],
            'MaxCost': instance['max_cost'],
            'MaxCostStrategy': instance['max_cost_strategy'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DestinationRateSerializer(serializers.Serializer):
    TPid = serializers.CharField(required=True)
    ID = serializers.CharField(required=True)
    DestinationRates = DestinationRatesSerializer(many=True, required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        destination_rates = DestinationRatesSerializer(
            data=instance['DestinationRates'],
            many=True,
        )

        if destination_rates.is_valid(raise_exception=True):
            destination_rates = destination_rates.data

        return {
            'tariff_plan_id': instance['TPid'],
            'id': instance['ID'],
            'destination_rates': destination_rates,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ReverseDestinationRateSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    destination_rates = ReverseDestinationRatesSerializer(
        many=True,
        required=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)
        destination_rates = ReverseDestinationRatesSerializer(
            data=instance['destination_rates'],
            many=True,
        )

        if destination_rates.is_valid(raise_exception=True):
            destination_rates = destination_rates.data

        return {
            'ID': CGRatesConventions.destination_rate(
                instance['id'],
            ),
            'DestinationRates': destination_rates,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ChargerProfileSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    RunID = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    FilterIDs = serializers.ListField(required=True, allow_null=True)
    AttributeIDs = serializers.ListField(required=True, allow_null=True)
    Weight = serializers.IntegerField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'tenant': instance['Tenant'],
            'filter_ids': instance['FilterIDs'],
            'attribute_ids': instance['AttributeIDs'],
            'run_id': instance['RunID'],
            'weight': instance['Weight'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SupplierSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    FilterIDs = serializers.ListField(required=True, allow_null=True)
    RatingPlanIDs = serializers.ListField(required=True, allow_null=True)
    ResourceIDs = serializers.ListField(required=True, allow_null=True)
    StatIDs = serializers.ListField(required=True, allow_null=True)
    Weight = serializers.IntegerField(required=True)
    Blocker = serializers.BooleanField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'filter_ids': instance['FilterIDs'],
            'rating_plan_ids': instance['RatingPlanIDs'],
            'resource_ids': instance['ResourceIDs'],
            'stat_ids': instance['StatIDs'],
            'weight': instance['Weight'],
            'blocker': instance['Blocker'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SupplierProfileSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    FilterIDs = serializers.ListField(required=True)
    Sorting = serializers.CharField(required=True)
    SortingParameters = serializers.ListField(required=True)
    Suppliers = SupplierSerializer(many=True, required=True)
    Weight = serializers.IntegerField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        suppliers = SupplierSerializer(
            data=instance['Suppliers'],
            many=True,
        )

        if suppliers.is_valid(raise_exception=True):
            suppliers = suppliers.data

        return {
            'id': instance['ID'],
            'tenant': instance['Tenant'],
            'filter_ids': instance['FilterIDs'],
            'sorting': instance['Sorting'],
            'sorting_parameters': instance['SortingParameters'],
            'weight': instance['Weight'],
            'suppliers': suppliers,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class FilterRulesSerializer(serializers.Serializer):
    Type = serializers.CharField(required=True)
    FieldName = serializers.CharField(required=True)
    Values = serializers.ListField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'type': instance['Type'],
            'field_name': instance['FieldName'],
            'values': instance['Values'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class FilterSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    Rules = FilterRulesSerializer(many=True, required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        rules = FilterRulesSerializer(
            data=instance['Rules'],
            many=True,
        )

        if rules.is_valid(raise_exception=True):
            rules = rules.data

        return {
            'id': instance['ID'],
            'tenant': instance['Tenant'],
            'rules': rules,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ActiveSessionsV1Serializer(serializers.Serializer):
    CGRID = serializers.CharField(required=True)
    Account = serializers.CharField(required=True)
    Usage = serializers.IntegerField(required=True)
    MaxCostSoFar = serializers.FloatField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'cgr_id': instance['CGRID'],
            'account': instance['Account'],
            'usage': instance['Usage'],
            'cost': instance['MaxCostSoFar'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ThresholdProfileSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    MaxHits = serializers.IntegerField(required=True)
    MinHits = serializers.IntegerField(required=True)
    MinSleep = serializers.IntegerField(required=True)
    Weight = serializers.IntegerField(required=True)
    FilterIDs = serializers.ListField(required=True)
    ActionIDs = serializers.ListField(required=True)
    Async = serializers.BooleanField(required=True)
    Blocker = serializers.BooleanField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'id': instance['ID'],
            'tenant': instance['Tenant'],
            'max_hits': instance['MaxHits'],
            'min_hits': instance['MinHits'],
            'min_sleeps': instance['MinSleep'],
            'weight': instance['Weight'],
            'filter_ids': instance['FilterIDs'],
            'action_ids': instance['ActionIDs'],
            'async': instance['Async'],
            'blocker': instance['Blocker'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DestinationSerializer(serializers.Serializer):
    Id = serializers.CharField(required=True)
    Prefixes = serializers.ListField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'id': instance['Id'],
            'prefixes': instance['Prefixes'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class AttributeValueSerializer(serializers.Serializer):
    Rules = serializers.CharField(required=True)
    AllFiltersMatch = serializers.BooleanField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'rules': instance['Rules'],
            'all_filters_match': instance['AllFiltersMatch'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class AttributeSerializer(serializers.Serializer):
    FilterIDs = serializers.ListField(
        required=True,
        allow_null=True,
    )
    Path = serializers.CharField(required=False, allow_blank=True)
    Type = serializers.CharField(required=True)
    Value = AttributeValueSerializer(many=True, required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        value = AttributeValueSerializer(
            data=instance['Value'],
            many=True,
        )

        if value.is_valid(raise_exception=True):
            value = value.data

        return {
            'path': instance['Path'],
            'filter_ids': instance['FilterIDs'],
            'value': value,
            'type': instance['Type'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class AttributeProfileSerializer(serializers.Serializer):
    """
    Get AttributeProfile from actions in cgrates
    """
    Tenant = serializers.CharField(required=True)
    ID = serializers.CharField(required=True)
    Blocker = serializers.BooleanField(required=True)
    Weight = serializers.IntegerField(required=True)
    ActivationInterval = serializers.CharField(required=True, allow_null=True)
    Contexts = serializers.ListField(
        required=True,
        allow_null=True,
    )
    FilterIDs = serializers.ListField(
        required=True,
        allow_null=True,
    )
    Attributes = AttributeSerializer(many=True, required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        attributes = AttributeSerializer(
            many=True,
            data=instance['Attributes'],
        )

        if attributes.is_valid(raise_exception=True):
            attributes = attributes.data

        return {
            'tenant': instance['Tenant'],
            'id': instance['ID'],
            'filter_ids': instance['FilterIDs'],
            'activation_interval': instance['ActivationInterval'],
            'attributes': attributes,
            'weight': instance['Weight'],
            'blocker': instance['Blocker'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ActionsV1Serializer(serializers.Serializer):
    """
    Get actions v1 (base balance) from action topup_reset in cgrates
    """
    Identifier = serializers.ChoiceField(
        required=True,
        choices=['*topup_reset'],
    )
    Units = serializers.CharField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'id': instance['Identifier'],
            'value': instance['Units'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ActionsV2BalanceValueSerializer(serializers.Serializer):
    """
    Get balance value from actions in cgrates
    """
    Method = serializers.CharField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    Params = serializers.CharField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    Static = serializers.CharField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'method': instance['Method'],
            'params': instance['Params'],
            'static': instance['Static'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ActionsV2BalanceSerializer(serializers.Serializer):
    """
    Get balance from actions in cgrates
    """
    Uuid = serializers.CharField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    ID = serializers.CharField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    Type = serializers.CharField(
        required=True,
        allow_blank=True,
        allow_null=True,
    )
    Value = ActionsV2BalanceValueSerializer(required=True, allow_null=True)

    def to_representation(self, instance):
        instance = dict(instance)
        balance_value = None
        if instance['Value'] is not None:
            balance_value = ActionsV2BalanceValueSerializer(
                data=instance['Value']
            )

            if balance_value.is_valid(raise_exception=True):
                balance_value = balance_value.data

        return {
            'uuid': instance['Uuid'],
            'id': instance['ID'],
            'type': instance['Type'],
            'value': balance_value,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ActionsV2Serializer(serializers.Serializer):
    """
    Get actions in cgrates
    """
    Id = serializers.CharField(required=True)
    ActionType = serializers.CharField(required=True)
    ExtraParameters = serializers.CharField(required=True, allow_blank=True)
    Filter = serializers.CharField(required=True, allow_blank=True)
    ExpirationString = serializers.CharField(required=True, allow_blank=True)
    Weight = serializers.IntegerField(required=True)
    Balance = ActionsV2BalanceSerializer(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        balance = ActionsV2BalanceSerializer(data=instance["Balance"])
        if balance.is_valid(raise_exception=True):
            balance = balance.data
        return {
            'id': instance['Id'],
            'action_type': instance['ActionType'],
            'extra_parameters': instance['ExtraParameters'],
            'filter': instance['Filter'],
            'expiration_string': instance['ExpirationString'],
            'weight': instance['Weight'],
            'balance': balance,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BalanceSerializer(serializers.Serializer):
    """
    Get balance from cgrates
    """
    ID = serializers.CharField(required=True)
    Uuid = serializers.CharField(required=True)
    Value = serializers.CharField(required=True)
    ExpirationDate = serializers.CharField(required=True)
    Weight = serializers.IntegerField(required=True)
    Disabled = serializers.BooleanField(required=True)
    Blocker = serializers.BooleanField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'uuid': instance['Uuid'],
            'id': instance['ID'],
            'value': instance['Value'],
            'expiration_date': instance['ExpirationDate'],
            'weight': instance['Weight'],
            'disabled': instance['Disabled'],
            'blocker': instance['Blocker'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class AccountSerializer(serializers.Serializer):
    """
    Get account details from cgrates
    """
    ID = serializers.CharField(required=True)
    Disabled = serializers.BooleanField(required=True)
    AllowNegative = serializers.BooleanField(required=True)
    BalanceMap = serializers.DictField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        balance_map = BalanceSerializer(
            data=instance['BalanceMap']['*monetary'],
            many=True,
        )

        if not balance_map.is_valid():
            raise serializers.ValidationError(balance_map.errors)

        return {
            'id': instance['ID'],
            'disabled': instance['Disabled'],
            'allow_negative': instance['AllowNegative'],
            'balance_map': balance_map.data,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BalanceSummariesSerializer(serializers.Serializer):
    UUID = serializers.CharField(required=True)
    ID = serializers.CharField(required=True)
    Type = serializers.CharField(required=True)
    Value = serializers.CharField(required=True)
    Disabled = serializers.BooleanField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        return {
            'uuid': instance['UUID'],
            'id': instance['ID'],
            'type': instance['Type'],
            'Value': instance['Value'],
            'disabled': instance['Disabled'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRsAccountSummarySerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    AllowNegative = serializers.BooleanField(required=True)
    Disabled = serializers.BooleanField(required=True)
    BalanceSummaries = BalanceSummariesSerializer(required=True, many=True)

    def to_representation(self, instance):
        instance = dict(instance)
        balance_summaries = BalanceSummariesSerializer(
            data=instance['BalanceSummaries'],
            many=True,
        )

        if balance_summaries.is_valid(raise_exception=True):
            balance_summaries = balance_summaries.data

        return {
            'id': instance['ID'],
            'disabled': instance['Disabled'],
            'allow_negative': instance['AllowNegative'],
            'balance_summaries': balance_summaries,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class IncrementsSerializer(serializers.Serializer):
    """
    A single Increment from Charge from CostDetails of CDR
    """
    Usage = serializers.CharField(required=True)
    Cost = serializers.CharField(required=True)
    AccountingID = serializers.CharField(required=True)
    CompressFactor = serializers.CharField(required=True)

    def to_representation(self, instance):
        return {
            'usage': instance['Usage'],
            'cost': instance['Cost'],
            'accounting_id': instance['AccountingID'],
            'compress_factor': instance['CompressFactor'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRsTimingsSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    Years = serializers.ListField(required=True)
    Months = serializers.ListField(required=True)
    MonthDays = serializers.ListField(required=True)
    WeekDays = serializers.ListField(required=True)
    StartTime = serializers.CharField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'years': instance['Years'],
            'months': instance['Months'],
            'month_days': instance['MonthDays'],
            'week_days': instance['WeekDays'],
            'start_time': instance['StartTime'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RatesSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    GroupIntervalStart = serializers.CharField(required=True, allow_blank=True)
    RateIncrement = serializers.CharField(required=True, allow_blank=True)
    RateUnit = serializers.CharField(required=True, allow_blank=True)
    Value = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'group_interval_start': instance['GroupIntervalStart'],
            'rate_increment': instance['RateIncrement'],
            'rate_unit': instance['RateUnit'],
            'value': instance['Value'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRsRatingFiltersSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    DestinationID = serializers.CharField(required=True, allow_blank=True)
    DestinationPrefix = serializers.CharField(required=True, allow_blank=True)
    RatingPlanID = serializers.CharField(required=True, allow_blank=True)
    Subject = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'destination_id': instance['DestinationID'],
            'destination_prefix': instance['DestinationPrefix'],
            'subject': instance['Subject'],
            'rating_plan_id': instance['RatingPlanID'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRsRatingSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    ConnectFee = serializers.CharField(required=True, allow_blank=True)
    RoundingMethod = serializers.CharField(required=True, allow_blank=True)
    RoundingDecimals = serializers.CharField(required=True, allow_blank=True)
    MaxCost = serializers.CharField(required=True, allow_blank=True)
    MaxCostStrategy = serializers.CharField(required=True, allow_blank=True)
    TimingID = serializers.CharField(required=True, allow_blank=True)
    RatesID = serializers.CharField(required=True, allow_blank=True)
    RatingFiltersID = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'connect_fee': instance['ConnectFee'],
            'rounding_method': instance['RoundingMethod'],
            'rounding_decimals': instance['RoundingDecimals'],
            'max_cost': instance['MaxCost'],
            'max_cost_strategy': instance['MaxCostStrategy'],
            'timing_id': instance['TimingID'],
            'rates_id': instance['RatesID'],
            'rating_filters_id': instance['RatingFiltersID'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ExtraFieldsMinimalSerializer(serializers.Serializer):
    BalanceType = serializers.CharField(default="-", allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'balance_type':
                instance['BalanceType'] if 'BalanceType' in instance else "",
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ExtraFieldsSerializer(serializers.Serializer):
    cgr_flags = serializers.CharField(required=False, allow_blank=True)
    EventName = serializers.CharField(required=False, allow_blank=True)
    Supplier = serializers.CharField(required=False, allow_blank=True)
    DisconnectCause = serializers.CharField(required=False, allow_blank=True)
    OperatorName = serializers.CharField(default="-", allow_blank=True)
    CallDirection = serializers.CharField(default="-", allow_blank=True)
    BalanceType = serializers.CharField(default="-", allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'operator_name':
                instance['OperatorName'] if 'OperatorName' in instance else "",
            'call_direction':
                instance['CallDirection'] if
                'CallDirection' in instance else "",
            'event_name':
                instance['EventName'] if 'EventName' in instance else "",
            'supplier':
                instance['Supplier'] if 'Supplier' in instance else "",
            'balance_type':
                instance['BalanceType'] if 'BalanceType' in instance else "",
            'disconnect_cause': instance['DisconnectCause'] if
            'DisconnectCause' in instance else None,
            'cgr_flags':
                instance['cgr_flags'] if 'cgr_flags' in instance else "",
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRsAccountingSerializer(serializers.Serializer):
    ID = serializers.CharField(required=True)
    AccountID = serializers.CharField(required=True, allow_blank=True)
    BalanceUUID = serializers.CharField(required=True, allow_blank=True)
    RatingID = serializers.CharField(required=True, allow_blank=True)
    Units = serializers.CharField(required=True, allow_blank=True)
    ExtraChargeID = serializers.CharField(required=True, allow_blank=True)

    def to_representation(self, instance):
        instance = dict(instance)

        return {
            'id': instance['ID'],
            'account_id': instance['AccountID'],
            'balance_uuid': instance['BalanceUUID'],
            'rating_id': instance['RatingID'],
            'units': instance['Units'],
            'extra_charge_id': instance['ExtraChargeID'],
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRsChargesSerializer(serializers.Serializer):
    """
    A single Charge from CostDetails of CDR
    """
    RatingID = serializers.CharField(required=True)
    CompressFactor = serializers.CharField(required=True)
    Increments = IncrementsSerializer(required=True, many=True)

    def to_representation(self, instance):
        instance = dict(instance)
        increments_summary = IncrementsSerializer(
            data=instance['Increments'],
            many=True
        )

        if increments_summary.is_valid(raise_exception=True):
            increments_summary = increments_summary.data

        return {
            'rating_id': instance['RatingID'],
            'compress_factor': instance['CompressFactor'],
            'increments_summary': increments_summary,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CostDetailsSerializer(serializers.Serializer):
    """
    A single CostDetails from CDR of CGRateS
    """
    CGRID = serializers.CharField(required=True)
    RunID = serializers.CharField(required=True)
    StartTime = serializers.CharField(required=True)
    Usage = serializers.CharField(required=True, allow_null=True)
    Cost = serializers.CharField(required=True, allow_null=True)
    AccountSummary = CDRsAccountSummarySerializer(required=True)
    Charges = CDRsChargesSerializer(required=True, many=True)
    Accounting = serializers.DictField(required=True)
    Rating = serializers.DictField(required=True)
    RatingFilters = serializers.DictField(required=True)
    Timings = serializers.DictField(required=True)

    def to_representation(self, instance):
        instance = dict(instance)
        account_summary = CDRsAccountSummarySerializer(
            data=instance['AccountSummary'],
        )
        charges = CDRsChargesSerializer(
            data=instance['Charges'],
            many=True,
        )
        accounting = Tools.convert_dynamic_dict_to_list(
            original_dict=instance['Accounting'],
            replace_key='ID',
        )
        accounting = CDRsAccountingSerializer(
            data=accounting,
            many=True,
        )
        rating = Tools.convert_dynamic_dict_to_list(
            original_dict=instance['Rating'],
            replace_key='ID',
        )
        rating = CDRsRatingSerializer(
            data=rating,
            many=True,
        )

        rating_filters = Tools.convert_dynamic_dict_to_list(
            original_dict=instance['RatingFilters'],
            replace_key='ID',
        )
        rating_filters = CDRsRatingFiltersSerializer(
            data=rating_filters,
            many=True,
        )
        timings = Tools.convert_dynamic_dict_to_list(
            original_dict=instance['Timings'],
            replace_key='ID',
        )
        timings = CDRsTimingsSerializer(
            data=timings,
            many=True,
        )

        if account_summary.is_valid(raise_exception=True):
            account_summary = account_summary.data

        if charges.is_valid(raise_exception=True):
            charges = charges.data

        if accounting.is_valid(raise_exception=True):
            accounting = accounting.data

        if rating.is_valid(raise_exception=True):
            rating = rating.data

        if rating_filters.is_valid(raise_exception=True):
            rating_filters = rating_filters.data

        if timings.is_valid(raise_exception=True):
            timings = timings.data

        return {
            'cgr_id': instance['CGRID'],
            'run_id': instance['RunID'],
            'start_time': instance['StartTime'],
            'usage': instance['Usage'],
            'cost': instance['Cost'],
            'account_summary': account_summary,
            'charges': charges,
            'accounting': accounting,
            'rating': rating,
            'rating_filters': rating_filters,
            'timings': timings,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRMinimalSerializer(serializers.Serializer):
    """
    A single CDR from CGRateS (Minimal Version)
    id is the duplicate value of cgr_id
    this field added to use in front end panel and have no other usage
    """
    CGRID = serializers.CharField(required=True)
    RunID = serializers.CharField(required=True)
    OrderID = serializers.CharField(required=True)
    OriginHost = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    OriginID = serializers.CharField(required=True)
    Source = serializers.CharField(required=True)
    ToR = serializers.CharField(required=True)
    RequestType = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    Category = serializers.CharField(required=True)
    Account = serializers.CharField(required=True)
    CostSource = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    Usage = serializers.CharField(required=True)
    Destination = serializers.CharField(required=True)
    Cost = serializers.CharField(required=True)
    SetupTime = serializers.CharField(required=True)
    ExtraFields = ExtraFieldsMinimalSerializer(
        required=False,
        allow_null=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)

        extra_fields = ExtraFieldsMinimalSerializer(
            data=instance['ExtraFields'],
        )

        if extra_fields.is_valid(raise_exception=True):
            extra_fields = extra_fields.data

        return {
            'id': instance['CGRID'],
            'cgr_id': instance['CGRID'],
            'run_id': instance['RunID'],
            'order_id': instance['OrderID'],
            'origin_host': instance['OriginHost'],
            'origin_id': instance['OriginID'],
            'source': instance['Source'],
            'type_of_record': instance['ToR'],
            'tenant': instance['Tenant'],
            'request_type': instance['RequestType'],
            'category': instance['Category'],
            'account': instance['Account'],
            'cost_source': instance['CostSource'],
            'usage': instance['Usage'],
            'destination': instance['Destination'],
            'cost': instance['Cost'],
            'extra_fields': extra_fields,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CDRSerializer(serializers.Serializer):
    """
    A single CDR from CGRateS
    id is the duplicate value of cgr_id
    this field added to use in front end panel and have no other usage
    """
    CGRID = serializers.CharField(required=True)
    RunID = serializers.CharField(required=True)
    OrderID = serializers.CharField(required=True)
    OriginHost = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    OriginID = serializers.CharField(required=True)
    Source = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    ToR = serializers.CharField(required=True)
    RequestType = serializers.CharField(required=True)
    Tenant = serializers.CharField(required=True)
    Category = serializers.CharField(required=True)
    Account = serializers.CharField(required=True)
    CostSource = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    Usage = serializers.CharField(required=True)
    Destination = serializers.CharField(required=True)
    Cost = serializers.CharField(required=True)
    SetupTime = serializers.CharField(required=True)
    CostDetails = CostDetailsSerializer(
        required=False,
        allow_null=True,
    )
    ExtraFields = ExtraFieldsSerializer(
        required=False,
        allow_null=True,
    )

    def to_representation(self, instance):
        instance = dict(instance)
        cost_details = None
        if instance['CostDetails']:
            cost_details = CostDetailsSerializer(
                data=instance['CostDetails'],
            )
            if cost_details.is_valid(raise_exception=True):
                cost_details = cost_details.data

        extra_fields = None
        if instance['ExtraFields']:
            extra_fields = ExtraFieldsSerializer(
                data=instance['ExtraFields'],
            )
            if extra_fields.is_valid(raise_exception=True):
                extra_fields = extra_fields.data

        return {
            'id': instance['CGRID'],
            'cgr_id': instance['CGRID'],
            'run_id': instance['RunID'],
            'order_id': instance['OrderID'],
            'origin_host': instance['OriginHost'],
            'origin_id': instance['OriginID'],
            'source': instance['Source'],
            'type_of_record': instance['ToR'],
            'tenant': instance['Tenant'],
            'request_type': instance['RequestType'],
            'category': instance['Category'],
            'account': instance['Account'],
            'cost_source': instance['CostSource'],
            'usage': instance['Usage'],
            'destination': instance['Destination'],
            'cost': instance['Cost'],
            'setup_time': instance['SetupTime'],
            'cost_details': cost_details,
            'extra_fields': extra_fields,
        }

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ToggleSubscriptionSerializer(serializers.Serializer):
    """
    Toggle subscription body
    """
    status_code = serializers.ChoiceField(
        required=True,
        choices=['enable', 'disable'],
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
