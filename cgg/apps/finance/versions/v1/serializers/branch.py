from django.db.models import Count
from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Branch, Destination
from cgg.apps.finance.versions.v1.serializers.destination import (
    DestinationNamesSerializer,
    DestinationSerializer,
)
from cgg.core import api_exceptions
from cgg.core.tools import Tools


class BranchSerializer(serializers.ModelSerializer):
    destinations = DestinationSerializer(many=True, read_only=True)
    destination_names = serializers.ListField(required=False)
    branch_code = serializers.CharField(required=True)
    branch_name = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Branch
        fields = [
            'id',
            'branch_code',
            'branch_name',
            'destinations',
            'destination_names',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        try:
            validated_data['branch_code'] = Tools.to_snake_case(
                validated_data['branch_code'],
            )
            Branch.objects.get(
                branch_code=validated_data['branch_code'],
            )
            raise api_exceptions.Conflict409(
                _('A branch with this branch code is already exists')
            )
        except Branch.DoesNotExist:
            destination_names = []
            if 'destination_names' in validated_data:
                destination_names = validated_data.pop('destination_names')

            branch_object = Branch.objects.create(**validated_data)

            for destination_name in destination_names:
                destination_objects = Destination.objects.filter(
                    name=destination_name,
                )

                for destination_object in destination_objects:
                    if Branch.objects.filter(
                            destinations=destination_object
                    ).count() == 0:
                        branch_object.destinations.add(
                            destination_object
                        )

        return branch_object

    def update(self, instance, validated_data):
        if 'branch_code' in validated_data:
            validated_data.pop('branch_code')

        if 'destination_names' not in validated_data:
            raise api_exceptions.ValidationError400({
                'destination_names': _(
                    'Field is required to create new branch')
            })
        destination_names = validated_data.pop('destination_names')
        instance.destinations.clear()

        for destination_name in destination_names:
            destination_objects = Destination.objects.filter(
                name=destination_name,
            )

            for destination_object in destination_objects:
                if Branch.objects.filter(
                        destinations=destination_object
                ).count() == 0:
                    instance.destinations.add(
                        destination_object
                    )

        return super().update(instance, validated_data)


class BranchesSerializer(serializers.ModelSerializer):
    destinations = DestinationNamesSerializer(many=True, read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id',
            'branch_code',
            'branch_name',
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
            "branch_code": str(instance.branch_code),
            "branch_name": str(instance.branch_name),
            "destination": destinations.data,
            "created_at": instance.created_at.timestamp(),
            "updated_at": instance.updated_at.timestamp(),
        }
