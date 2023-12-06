from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Customer
from cgg.apps.finance.versions.v1.serializers.subscription import (
    SubscriptionsSerializer,
)
from cgg.core import api_exceptions


class CustomerSerializer(serializers.ModelSerializer):
    subscriptions = SubscriptionsSerializer(many=True, required=False)
    customer_code = serializers.CharField(required=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'prime_code',
            'credit',
            'customer_code',
            'created_at',
            'updated_at',
            'subscriptions',
        ]

    def create(self, validated_data):
        try:
            Customer.objects.get(
                customer_code=validated_data['customer_code'],
            )
            raise api_exceptions.Conflict409(
                _('A customer with this customer code is already exists')
            )
        except Customer.DoesNotExist:
            return Customer.objects.create(**validated_data)


class CustomersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id',
            'prime_code',
            'credit',
            'customer_code',
            'created_at',
            'updated_at',
        ]
