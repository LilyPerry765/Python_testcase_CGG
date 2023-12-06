from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Invoice
from cgg.apps.finance.versions.v1.serializers.payment import (
    MigratePaymentsSerializer,
)
from cgg.core.tools import Tools


class MigrateInvoiceSerializer(serializers.Serializer):
    subscription_code = serializers.CharField(required=True)
    subscription_fee = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    tax_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    tax_percent = serializers.IntegerField()
    debt = serializers.DecimalField(max_digits=20, decimal_places=2)
    discount = serializers.DecimalField(max_digits=20, decimal_places=2)
    mobile_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    mobile_usage = serializers.DecimalField(max_digits=20, decimal_places=2)
    landlines_long_distance_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    landlines_long_distance_usage = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    description = serializers.CharField(required=True)
    invoice_type = serializers.CharField(required=True)
    status_code = serializers.CharField(required=True)
    from_date = serializers.DateTimeField(required=True)
    to_date = serializers.DateTimeField(required=True)
    created_at = serializers.DateTimeField(required=True)
    updated_at = serializers.DateTimeField(required=True)
    payments = MigratePaymentsSerializer(required=True, many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class InvoiceSerializer(serializers.ModelSerializer):
    subscription_fee = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    tax_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    discount = serializers.DecimalField(max_digits=20, decimal_places=2)
    debt = serializers.DecimalField(max_digits=20, decimal_places=2)
    mobile_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    mobile_usage = serializers.DecimalField(max_digits=20, decimal_places=2)
    landlines_local_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    landlines_local_usage = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    landlines_corporate_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    landlines_corporate_usage = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    landlines_long_distance_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    landlines_long_distance_usage = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    international_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    international_usage = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    total_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_usage_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    total_usage_cost_prepaid = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    total_usage_cost_postpaid = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    total_usage_prepaid = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    total_usage_postpaid = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
    )
    total_usage = serializers.DecimalField(max_digits=20, decimal_places=2)
    customer_code = serializers.CharField(required=False)
    subscription_code = serializers.CharField(required=False)
    credit_invoice_id = serializers.CharField(required=False)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'prime_code',
            'customer_code',
            'subscription_code',
            'number',
            'tracking_code',
            'period_count',
            'tax_percent',
            'tax_cost',
            'discount',
            'discount_description',
            'debt',
            'subscription_fee',
            'landlines_corporate_cost',
            'landlines_corporate_usage',
            'landlines_local_cost',
            'landlines_local_usage',
            'landlines_long_distance_cost',
            'landlines_long_distance_usage',
            'mobile_usage',
            'mobile_cost',
            'international_usage',
            'international_cost',
            'landlines_corporate_cost_prepaid',
            'landlines_corporate_usage_prepaid',
            'landlines_local_cost_prepaid',
            'landlines_local_usage_prepaid',
            'landlines_long_distance_cost_prepaid',
            'landlines_long_distance_usage_prepaid',
            'mobile_usage_prepaid',
            'mobile_cost_prepaid',
            'international_usage_prepaid',
            'international_cost_prepaid',
            'total_usage_cost_postpaid',
            'total_usage_cost_prepaid',
            'total_usage_postpaid',
            'total_usage_prepaid',
            'total_usage',
            'total_usage_cost',
            'total_cost',
            'total_cost_rounded',
            'status_code',
            'on_demand',
            'invoice_type_code',
            'description',
            'from_date',
            'to_date',
            'created_at',
            'due_date',
            'is_overdue',
            'updated_status_at',
            'paid_at',
            'credit_invoice_id',
            'credit',
        ]


class ExportInvoiceSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            _('id'): Tools.to_string_for_export(
                instance.id,
            ),
            _('tracking code'): Tools.to_string_for_export(
                instance.tracking_code,
            ),
            _('prime code'): Tools.to_string_for_export(
                instance.prime_code,
            ),
            _('subscription code'): Tools.to_string_for_export(
                instance.subscription_code,
            ),
            _('number'): Tools.to_string_for_export(
                instance.number,
            ),
            _('period count'): Tools.to_string_for_export(
                instance.period_count,
            ),
            _('tax percent'): Tools.to_string_for_export(
                instance.tax_percent,
            ),
            _('tax cost'): Tools.to_string_for_export(
                instance.tax_cost,
            ),
            _('discount'): Tools.to_string_for_export(
                instance.discount,
            ),
            _('discount description'): Tools.to_string_for_export(
                instance.discount_description,
            ),
            _('debt'): Tools.to_string_for_export(
                instance.debt,
            ),
            _('subscription fee'): Tools.to_string_for_export(
                instance.subscription_fee,
            ),
            _('landlines corporate cost'): Tools.to_string_for_export(
                instance.landlines_corporate_cost,
            ),
            _('landlines corporate usage'):
                Tools.convert_nano_seconds_to_seconds(
                    instance.landlines_corporate_usage,
                ),
            _('landlines local cost'): Tools.to_string_for_export(
                instance.landlines_local_cost,
            ),
            _('landlines local usage'): Tools.convert_nano_seconds_to_seconds(
                instance.landlines_local_usage,
            ),
            _('landlines long distance cost'): Tools.to_string_for_export(
                instance.landlines_long_distance_cost,
            ),
            _('landlines long distance usage'):
                Tools.convert_nano_seconds_to_seconds(
                    instance.landlines_long_distance_usage,
                ),
            _('mobile usage'): Tools.convert_nano_seconds_to_seconds(
                instance.mobile_usage,
            ),
            _('mobile cost'): Tools.to_string_for_export(
                instance.mobile_cost,
            ),
            _('international usage'): Tools.convert_nano_seconds_to_seconds(
                instance.international_usage,
            ),
            _('international cost'): Tools.to_string_for_export(
                instance.international_cost,
            ),
            _('landlines corporate cost prepaid'): Tools.to_string_for_export(
                instance.landlines_corporate_cost_prepaid,
            ),
            _('landlines corporate usage prepaid'):
                Tools.convert_nano_seconds_to_seconds(
                    instance.landlines_corporate_usage_prepaid,
                ),
            _('landlines local cost prepaid'): Tools.to_string_for_export(
                instance.landlines_local_cost_prepaid,
            ),
            _('landlines local usage prepaid'):
                Tools.convert_nano_seconds_to_seconds(
                    instance.landlines_local_usage_prepaid,
                ),
            _('landlines long distance cost prepaid'):
                Tools.to_string_for_export(
                    instance.landlines_long_distance_cost_prepaid,
                ),
            _('landlines long distance usage prepaid'):
                Tools.convert_nano_seconds_to_seconds(
                    instance.landlines_long_distance_usage_prepaid,
                ),
            _('mobile usage prepaid'): Tools.convert_nano_seconds_to_seconds(
                instance.mobile_usage_prepaid,
            ),
            _('mobile cost prepaid'): Tools.to_string_for_export(
                instance.mobile_cost_prepaid,
            ),
            _('international usage prepaid'):
                Tools.convert_nano_seconds_to_seconds(
                    instance.international_usage_prepaid,
                ),
            _('international cost prepaid'): Tools.to_string_for_export(
                instance.international_cost_prepaid,
            ),
            _('total usage'): Tools.convert_nano_seconds_to_seconds(
                instance.total_usage,
            ),
            _('total usage cost'): Tools.to_string_for_export(
                instance.total_usage_cost,
            ),
            _('total cost'): Tools.to_string_for_export(
                instance.total_cost,
            ),
            _('status code'): Tools.to_string_for_export(
                instance.status_label,
            ),
            _('on demand'): Tools.to_string_for_export(
                instance.on_demand,
                is_boolean=True,
            ),
            _('invoice type'): Tools.to_string_for_export(
                instance.invoice_type_label,
            ),
            _('description'): Tools.to_string_for_export(
                instance.description,
            ),
            _('credit invoice id'): Tools.to_string_for_export(
                instance.credit_invoice_id,
            ),
            _('from date'): Tools.to_jalali_date(
                instance.from_date,
            ),
            _('to date'): Tools.to_jalali_date(
                instance.to_date,
            ),
            _('created at'): Tools.to_jalali_date(
                instance.created_at,
            ),
            _('due date'): Tools.to_jalali_date(
                instance.due_date,
            ),
            _('updated status at'): Tools.to_jalali_date(
                instance.updated_status_at,
            ),
            _('paid at'): Tools.to_jalali_date(
                instance.paid_at,
            ),
        }

    class Meta:
        model = Invoice
