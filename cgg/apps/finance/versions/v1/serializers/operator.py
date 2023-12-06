from django.db.models import Count
from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Destination, Operator
from cgg.apps.finance.versions.v1.serializers.destination import (
    DestinationNamesSerializer,
    DestinationSerializer,
)
from cgg.core import api_exceptions
from cgg.core.tools import Tools


class OperatorsSerializer(serializers.ModelSerializer):
    destinations = DestinationNamesSerializer(many=True, read_only=True)

    class Meta:
        model = Operator
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )
        fields = [
            'id',
            'operator_code',
            'rate_time_type',
            'rate_time',
            'inbound_rate',
            'outbound_rate',
            'inbound_divide_on_percent',
            'outbound_divide_on_percent',
            'destinations',
            'created_at',
            'updated_at',
        ]

    def to_representation(self, instance):
        destinations = DestinationNamesSerializer(
            instance.destinations.values(
                'name',
                'country_code',
            ).annotate(
                prefixes_count=Count('prefix'),
            ),
            many=True,
        )

        return {
            "id": str(instance.id),
            "operator_code": str(instance.operator_code),
            "rate_time_type": str(instance.rate_time_type),
            "rate_time": instance.rate_time,
            "inbound_rate": str(instance.inbound_rate),
            "outbound_rate": str(instance.outbound_rate),
            "inbound_divide_on_percent": instance.inbound_divide_on_percent,
            "outbound_divide_on_percent": instance.outbound_divide_on_percent,
            "destination": destinations.data,
            "created_at": instance.created_at.timestamp(),
            "updated_at": instance.updated_at.timestamp(),
        }


class OperatorSerializer(serializers.ModelSerializer):
    destination_names = serializers.ListField(required=False)
    destinations = DestinationSerializer(many=True, read_only=True)

    class Meta:
        model = Operator
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )
        fields = [
            'id',
            'operator_code',
            'rate_time_type',
            'rate_time',
            'inbound_rate',
            'outbound_rate',
            'inbound_divide_on_percent',
            'outbound_divide_on_percent',
            'destination_names',
            'destinations',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        try:
            validated_data['operator_code'] = Tools.snake_case_to_camelcase(
                validated_data['operator_code'],
            )
            Operator.objects.get(
                operator_code=validated_data['operator_code'],
            )
            raise api_exceptions.Conflict409(
                _('A operator with this code is already exists')
            )
        except Operator.DoesNotExist:
            if 'destination_names' in validated_data:
                destination_names = validated_data.pop('destination_names')
            else:
                raise api_exceptions.ValidationError400({
                    'destination_names': _('This field is required')
                })

            operator_object = Operator.objects.create(**validated_data)

            for destination_name in destination_names:
                destination_objects = Destination.objects.filter(
                    name=destination_name,
                )

                for destination_object in destination_objects:
                    if Operator.objects.filter(
                            destinations=destination_object
                    ).count() == 0:
                        operator_object.destinations.add(
                            destination_object
                        )

        return operator_object

    def update(self, instance, validated_data):
        if 'operator_code' in validated_data:
            validated_data.pop('operator_code')

        if 'destination_names' not in validated_data:
            raise api_exceptions.ValidationError400({
                'destination_names': _('Required field to create new '
                                       'operator')
            })
        destination_names = validated_data.pop('destination_names')
        instance.destinations.clear()

        for destination_name in destination_names:
            destination_objects = Destination.objects.filter(
                name=destination_name,
            )
            for destination_object in destination_objects:
                if Operator.objects.filter(
                        destinations=destination_object
                ).count() == 0:
                    instance.destinations.add(
                        destination_object
                    )

        return super().update(instance, validated_data)
