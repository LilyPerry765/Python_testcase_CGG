import uuid
from datetime import datetime
from decimal import Decimal

from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import BaseBalanceInvoice
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.payment import (
    MigratePaymentsSerializer,
)
from cgg.core.tools import Tools


class MigrateBaseBalanceInvoiceSerializer(serializers.Serializer):
    subscription_code = serializers.CharField(required=True)
    total_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    status_code = serializers.CharField(required=True)
    created_at = serializers.DateTimeField(required=True)
    updated_at = serializers.DateTimeField(required=True)
    payments = MigratePaymentsSerializer(required=True, many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class BaseBalanceInvoiceSerializer(serializers.ModelSerializer):
    # On fly field to check whether an decrease must return to credit or not
    to_credit = serializers.BooleanField(default=True)
    total_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    subscription_code = serializers.CharField(required=False)
    credit_invoice_id = serializers.CharField(required=False)
    operation_type = serializers.ChoiceField(
        default=FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
        choices=[
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
        ],
    )

    class Meta:
        model = BaseBalanceInvoice
        fields = [
            'id',
            'prime_code',
            'subscription_code',
            'number',
            'credit_invoice_id',
            'operation_type',
            'tracking_code',
            'status_code',
            'total_cost',
            'description',
            'created_at',
            'updated_status_at',
            'paid_at',
            'to_credit',
        ]
        read_only_fields = (
            'id',
            'prime_code',
            'credit_invoice_id',
            'created_at',
            'updated_at',
            'updated_status_at',
            'status_code',
            'tracking_code',
        )

    def validate(self, attrs):
        if Decimal(attrs['total_cost']) <= 0:
            raise serializers.ValidationError(
                {
                    "total_cost": _("Can not be empty or less than zero")
                }
            )
        if attrs['operation_type'] == \
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0]:
            attrs['total_cost'] = Tools.make_safe_payment_amount(
                attrs['total_cost']
            )

        return attrs

    def create(self, validated_data):
        if validated_data['operation_type'] == \
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0]:
            validated_data['status_code'] = \
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0]
            validated_data['paid_at'] = None
        else:
            validated_data['status_code'] = \
                FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
            validated_data['paid_at'] = datetime.now()
            validated_data['description'] = _(
                "This base balance invoice is generated automatically to "
                "decrease subscription's base balance"
            )
        validated_data['updated_status_at'] = datetime.now()
        validated_data['tracking_code'] = uuid.uuid4()
        validated_data['subscription_id'] = \
            self.initial_data['subscription_id']

        if 'subscription_code' in validated_data:
            validated_data.pop('subscription_code')

        if 'to_credit' in validated_data:
            validated_data.pop('to_credit')

        return BaseBalanceInvoice.objects.create(**validated_data)

    def to_representation(self, instance):
        instance = dict(
            super(BaseBalanceInvoiceSerializer, self).to_representation(
                instance
            )
        )
        instance.pop('to_credit')

        return instance


class BaseBalanceInvoicesSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    subscription_code = serializers.CharField(required=False)

    class Meta:
        model = BaseBalanceInvoice
        fields = [
            'id',
            'prime_code',
            'subscription_code',
            'number',
            'tracking_code',
            'operation_type',
            'status_code',
            'created_at',
            'updated_status_at',
            'paid_at',
            'total_cost',
        ]


class BaseBalanceInvoiceExportSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            _('id'): Tools.to_string_for_export(instance.id),
            _('tracking code'): Tools.to_string_for_export(
                instance.tracking_code,
            ),
            _('prime code'): instance.prime_code,
            _('subscription code'): instance.subscription_code,
            _('number'): instance.number,
            _('credit invoice id'): Tools.to_string_for_export(
                instance.credit_invoice_id,
            ),
            _('operation type'): Tools.to_string_for_export(
                Tools.translator(instance.operation_type),
            ),
            _('status code'): instance.status_label,
            _('total cost'): Tools.to_string_for_export(
                instance.total_cost,
            ),
            _('description'): instance.description,
            _('created at'): Tools.to_jalali_date(
                instance.created_at,
            ),
            _('updated status at'): Tools.to_jalali_date(
                instance.updated_status_at,
            ),
            _('paid at'): Tools.to_jalali_date(
                instance.paid_at,
            ),
        }

    class Meta:
        model = BaseBalanceInvoice
