from rest_framework import serializers

from cgg.apps.finance.models import Destination


class DestinationNamesSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    country_code = serializers.CharField(required=True)
    prefixes_count = serializers.IntegerField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            'id',
            'code',
            'prefix',
            'name',
            'country_code',
            'created_at',
            'updated_at',
        ]

    def update(self, instance, validated_data):
        if 'code' in validated_data:
            validated_data.pop('code')

        if 'prefix' in validated_data:
            validated_data.pop('prefix')

        return super().update(instance, validated_data)
