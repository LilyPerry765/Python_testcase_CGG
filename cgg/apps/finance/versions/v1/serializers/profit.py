from datetime import datetime

from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Profit
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.tools import Tools


class CreateProfitSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    operator_id = serializers.UUIDField(required=True)
    from_date = serializers.CharField(required=True)
    to_date = serializers.CharField(required=True)

    def validate(self, attrs):
        if isinstance(attrs['from_date'], str):
            try:
                attrs['from_date'] = datetime.fromtimestamp(
                    float(attrs['from_date']),
                )
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'from_date': _('Parse error for timestamp')
                })
        if isinstance(attrs['to_date'], str):
            try:
                attrs['to_date'] = datetime.fromtimestamp(
                    float(attrs['to_date']),
                )
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'to_date': _('Parse error for timestamp')
                })

        if attrs['from_date'] > attrs['to_date']:
            raise serializers.ValidationError({
                'from_date': _("Start date can not be greater than end date")
            })
        attrs['operator_id'] = Tools.uuid_validation(
            attrs['operator_id'],
        )
        attrs['from_date'] = str(
            attrs['from_date'].timestamp(),
        )
        attrs['to_date'] = str(
            attrs['to_date'].timestamp(),
        )

        return attrs


class ProfitsSerializer(serializers.ModelSerializer):
    operator_id = serializers.UUIDField(required=True)
    operator_code = serializers.CharField(required=False)
    from_date = serializers.DateTimeField(required=True)
    to_date = serializers.DateTimeField(required=True)
    updated_status_at = serializers.DateTimeField(required=True)
    status_code = serializers.ChoiceField(
        required=False,
        choices=[
            FinanceConfigurations.Profit.STATE_CHOICES[0][0],
            FinanceConfigurations.Profit.STATE_CHOICES[1][0],
            FinanceConfigurations.Profit.STATE_CHOICES[2][0],
        ],
    )
    total_cost_inbound = serializers.DecimalField(
        max_digits=20,
        read_only=True,
        decimal_places=2,
    )
    total_cost_outbound = serializers.DecimalField(
        max_digits=20,
        read_only=True,
        decimal_places=2,
    )
    total_usage = serializers.DecimalField(
        max_digits=20,
        read_only=True,
        decimal_places=2,
    )

    class Meta:
        model = Profit
        read_only_fields = (
            'id',
            'created_at',
            'updated_status_at',
        )
        fields = [
            'id',
            'operator_id',
            'operator_code',
            'inbound_used_percent',
            'outbound_used_percent',
            'total_cost_inbound',
            'total_cost_outbound',
            'total_usage',
            'from_date',
            'to_date',
            'status_code',
            'updated_status_at',
            'created_at',
        ]


class ProfitSerializer(serializers.ModelSerializer):
    operator_id = serializers.UUIDField(required=True)
    operator_code = serializers.CharField(required=False)
    from_date = serializers.DateTimeField(required=True)
    to_date = serializers.DateTimeField(required=True)
    updated_status_at = serializers.DateTimeField(required=True)
    status_code = serializers.ChoiceField(
        required=False,
        choices=[
            FinanceConfigurations.Profit.STATE_CHOICES[0][0],
            FinanceConfigurations.Profit.STATE_CHOICES[1][0],
            FinanceConfigurations.Profit.STATE_CHOICES[2][0],
        ],
    )
    total_cost_inbound = serializers.DecimalField(
        max_digits=20,
        read_only=True,
        decimal_places=2,
    )
    total_cost_outbound = serializers.DecimalField(
        max_digits=20,
        read_only=True,
        decimal_places=2,
    )
    total_usage = serializers.DecimalField(
        max_digits=20,
        read_only=True,
        decimal_places=2,
    )

    def update(self, instance, validated_data):
        if 'status_code' not in validated_data:
            raise serializers.ValidationError({
                'status_code': _("This field is required")
            })
        status_code = validated_data.pop('status_code')
        if instance.status_code != \
                FinanceConfigurations.Profit.STATE_CHOICES[0][0]:
            raise api_exceptions.Conflict409(
                ErrorMessages.PROFIT_409,
            )
        if instance.status_code == status_code:
            raise api_exceptions.Conflict409(
                ErrorMessages.PROFIT_409_SAME,
            )
        # Only update the status code not anything else
        return super().update(instance, {
            'status_code': status_code,
            'updated_status_at': datetime.now(),
        })

    class Meta:
        model = Profit
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'updated_status_at',
        )
        fields = [
            'id',
            'operator_id',
            'operator_code',
            'inbound_used_percent',
            'outbound_used_percent',
            'inbound_cost_first_part',
            'inbound_cost_second_part',
            'outbound_cost_first_part',
            'outbound_cost_second_part',
            'total_cost_inbound',
            'total_cost_outbound',
            'inbound_usage',
            'outbound_usage',
            'total_usage',
            'from_date',
            'to_date',
            'status_code',
            'updated_status_at',
            'created_at',
            'updated_at',
        ]


class ProfitExportSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            _('id'): Tools.to_string_for_export(instance.id),
            _('operator id'): Tools.to_string_for_export(instance.operator_id),
            _('operator code'): instance.operator_code,
            _('inbound used percent'): Tools.to_string_for_export(
                instance.inbound_used_percent,
            ),
            _('outbound used percent'): Tools.to_string_for_export(
                instance.outbound_used_percent,
            ),
            _('inbound usage'): Tools.to_string_for_export(
                instance.inbound_usage,
            ),
            _('outbound usage'): Tools.to_string_for_export(
                instance.outbound_usage,
            ),
            _('inbound cost first part'): Tools.to_string_for_export(
                instance.inbound_cost_first_part,
            ),
            _('inbound cost second part'): Tools.to_string_for_export(
                instance.inbound_cost_second_part,
            ),
            _('outbound cost first part'): Tools.to_string_for_export(
                instance.outbound_cost_first_part,
            ),
            _('outbound cost second part'): Tools.to_string_for_export(
                instance.outbound_cost_second_part,
            ),
            _('total cost inbound'): Tools.to_string_for_export(
                instance.total_cost_inbound,
            ),
            _('total cost outbound'): Tools.to_string_for_export(
                instance.total_cost_outbound,
            ),
            _('total usage'): Tools.to_string_for_export(
                instance.total_usage,
            ),
            _('from date'): Tools.to_jalali_date(instance.from_date),
            _('to date'): Tools.to_jalali_date(instance.to_date),
            _('status code'): instance.status_code,
            _('updated status at'): Tools.to_jalali_date(
                instance.updated_status_at
            ),
            _('created at'): Tools.to_jalali_date(instance.created_at),
            _('updated at'): Tools.to_jalali_date(instance.updated_at),
        }

    class Meta:
        model = Profit
