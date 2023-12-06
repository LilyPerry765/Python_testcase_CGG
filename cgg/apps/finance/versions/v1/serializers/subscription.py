from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Subscription
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core import api_exceptions


class ChangeBalanceSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    value = serializers.IntegerField(required=True)


class SubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id',
            'prime_code',
            'subscription_code',
            'subscription_type',
            'number',
            'is_allocated',
            'deallocated_at',
            'latest_paid_at',
            'auto_pay',
            'created_at',
            'updated_at',
        ]


class SubscriptionUpdateSerializer(serializers.Serializer):
    base_balance = serializers.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=20,
    )
    used_balance = serializers.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=20,
    )
    credit = serializers.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=20,
        default=0,
    )
    auto_pay = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionBaseBalanceSerializer(serializers.Serializer):
    value = serializers.DecimalField(
        required=True,
        decimal_places=2,
        max_digits=20,
    )
    # On fly field to check whether an decrease must return to credit or not
    to_credit = serializers.BooleanField(default=True)
    operation_type = serializers.ChoiceField(
        default=FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
        choices=[
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
        ],
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionConvertSerializer(serializers.Serializer):
    base_balance = serializers.DecimalField(
        required=True,
        decimal_places=2,
        max_digits=20,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionDeallocationSerializer(serializers.Serializer):
    cause = serializers.ChoiceField(
        default=FinanceConfigurations.Subscription.DEALLOCATION_CAUSE[0][0],
        choices=[
            FinanceConfigurations.Subscription.DEALLOCATION_CAUSE[0][0],
            FinanceConfigurations.Subscription.DEALLOCATION_CAUSE[1][0],
        ],
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionAntiSerializer(serializers.Serializer):
    """
    It's the result of an anti pattern.
    @TODO: Remove this
    """
    subscription_codes = serializers.ListField(
        required=False,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionSerializer(serializers.ModelSerializer):
    used_balance_postpaid = serializers.SerializerMethodField()
    current_balance_postpaid = serializers.SerializerMethodField()
    base_balance_postpaid = serializers.SerializerMethodField()
    base_balance_prepaid = serializers.SerializerMethodField()
    used_balance_prepaid = serializers.SerializerMethodField()
    current_balance_prepaid = serializers.SerializerMethodField()
    customer_id = serializers.UUIDField(required=True)
    branch_id = serializers.UUIDField(required=True)
    subscription_code = serializers.CharField(required=True)
    subscription_type = serializers.ChoiceField(
        required=True,
        choices=[
            FinanceConfigurations.Subscription.TYPE[0][0],
            FinanceConfigurations.Subscription.TYPE[1][0],
            FinanceConfigurations.Subscription.TYPE[2][0],
        ],
    )
    number = serializers.CharField(required=True)
    credit = serializers.DecimalField(
        required=False,
        decimal_places=2,
        max_digits=20,
    )
    is_allocated = serializers.BooleanField(required=True)
    auto_pay = serializers.BooleanField(default=True)

    def get_used_balance_prepaid(self, obj):
        if self.context:
            return self.context.get("used_balance_prepaid")
        return None

    def get_current_balance_prepaid(self, obj):
        if self.context:
            return self.context.get("current_balance_prepaid")
        return None

    def get_base_balance_prepaid(self, obj):
        if self.context:
            return self.context.get("base_balance_prepaid")
        return None

    def get_used_balance_postpaid(self, obj):
        if self.context:
            return self.context.get("used_balance_postpaid")
        return None

    def get_current_balance_postpaid(self, obj):
        if self.context:
            return self.context.get("current_balance_postpaid")
        return None

    def get_base_balance_postpaid(self, obj):
        if self.context:
            return self.context.get("base_balance_postpaid")
        return None

    class Meta:
        model = Subscription
        fields = [
            'id',
            'branch_id',
            'customer_id',
            'prime_code',
            'subscription_code',
            'subscription_type',
            'number',
            'credit',
            'base_balance_postpaid',
            'base_balance_prepaid',
            'used_balance_postpaid',
            'used_balance_prepaid',
            'current_balance_postpaid',
            'current_balance_prepaid',
            'is_allocated',
            'deallocated_at',
            'deallocation_cause',
            'latest_paid_at',
            'auto_pay',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        if Subscription.objects.filter(
                subscription_code=validated_data['subscription_code']
        ).count():
            raise api_exceptions.Conflict409(
                _(
                    'A subscription with this subscription code is already '
                    'exists',
                )
            )
        if Subscription.objects.filter(
                number=validated_data['number'],
                is_allocated=True,
        ).count():
            raise api_exceptions.Conflict409(
                _(
                    'An active subscription with this number is already '
                    'exists',
                )
            )

        return Subscription.objects.create(**validated_data)
