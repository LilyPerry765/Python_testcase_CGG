import uuid
from datetime import datetime
from decimal import Decimal

from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import (
    BaseBalanceInvoice,
    CreditInvoice,
    Invoice,
    PackageInvoice,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.payment import (
    PaymentsSerializer,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.tools import Tools


class MigrateCreditInvoiceSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(
        required=False,
        max_digits=20,
        decimal_places=2,
        default=0,
    )
    operation_type = serializers.ChoiceField(
        required=True,
        choices=[
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
        ],
    )
    payments = PaymentsSerializer(required=False, many=True)
    customer_code = serializers.CharField(required=False)

    class Meta:
        model = CreditInvoice
        fields = [
            'id',
            'customer_code',
            'tracking_code',
            'status_code',
            'status_label',
            'used_for',
            'used_for_id',
            'operation_type',
            'total_cost',
            'description',
            'created_at',
            'updated_status_at',
            'paid_at',
            'payments',
        ]
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'updated_status_at',
            'status_code',
            'tracking_code',
            'payments',
        )

    def create(self, validated_data):
        validated_data['status_code'] = \
            FinanceConfigurations.Invoice.STATE_CHOICES[0][0]
        validated_data['updated_status_at'] = datetime.now()
        validated_data['tracking_code'] = uuid.uuid4()
        validated_data['paid_at'] = None
        validated_data['customer_id'] = \
            self.initial_data['customer_id']

        if all(x in validated_data for x in ["used_for", "used_for_id"]) and \
                validated_data['used_for'] and validated_data['used_for_id']:
            # Check for data
            Tools.uuid_validation(validated_data['used_for_id'])
            if validated_data['used_for'] == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                invoice_class = Invoice
            elif validated_data['used_for'] == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                invoice_class = BaseBalanceInvoice
            else:
                invoice_class = PackageInvoice
            try:
                invoice_object = invoice_class.objects.get(
                    id=validated_data['used_for_id']
                )
                validated_data['total_cost'] = invoice_object.total_cost
            except invoice_class.DoesNotExist:
                raise api_exceptions.NotFound404(
                    f"{validated_data['used_for_id']} "
                    f"{ErrorMessages.GENERIC_404}"
                )

        return CreditInvoice.objects.create(**validated_data)


class CreditInvoiceSerializer(serializers.ModelSerializer):
    # is_hybrid is an on-fly field to handle hybrid payments
    is_hybrid = serializers.BooleanField(required=False, default=False)
    total_cost = serializers.DecimalField(
        required=False,
        max_digits=20,
        decimal_places=2,
        default=0,
    )
    operation_type = serializers.ChoiceField(
        required=True,
        choices=[
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
            FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
        ],
    )
    payments = PaymentsSerializer(required=False, many=True)
    customer_code = serializers.CharField(required=False)

    class Meta:
        model = CreditInvoice
        fields = [
            'id',
            'prime_code',
            'customer_code',
            'subscription_code',
            'number',
            'tracking_code',
            'status_code',
            'used_for',
            'used_for_id',
            'operation_type',
            'is_hybrid',
            'total_cost',
            'description',
            'created_at',
            'updated_status_at',
            'paid_at',
            'payments',
        ]
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'prime_code',
            'subscription_code',
            'number',
            'updated_status_at',
            'status_code',
            'is_hybrid',
            'tracking_code',
            'payments',
        )

    def to_representation(self, instance):
        representation_result = super().to_representation(instance)

        if "is_hybrid" in representation_result:
            representation_result.pop("is_hybrid")

        return representation_result

    def validate(self, attrs):
        if all(x in attrs for x in ["used_for", "used_for_id"]) and \
                attrs['used_for'] and attrs['used_for_id']:
            # Check for data
            Tools.uuid_validation(attrs['used_for_id'])
            if attrs['used_for'] == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                invoice_class = Invoice
                conflict_message_payed = _("This invoice is already payed")
                conflict_message_revoked = _("This invoice is already revoked")
            elif attrs['used_for'] == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                invoice_class = BaseBalanceInvoice
                conflict_message_payed = _(
                    "This base balance invoice is already payed",
                )
                conflict_message_revoked = _(
                    "This base balance invoice is already revoked",
                )
            else:
                invoice_class = PackageInvoice
                conflict_message_payed = _(
                    "This package invoice is already payed",
                )
                conflict_message_revoked = _(
                    "This package invoice is already revoked",
                )
            try:
                invoice_object = invoice_class.objects.get(
                    id=attrs['used_for_id']
                )
                if type(invoice_object) == PackageInvoice and len(
                        PackageInvoice.objects.filter(
                            subscription=invoice_object.subscription,
                            is_active=True,
                        )) > 0:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.PACKAGE_INVOICE_409,
                    )
                if attrs['is_hybrid'] and attrs['operation_type'] == \
                        FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][
                            0]:
                    # Check for hybrid payment
                    if Decimal(invoice_object.subscription.customer.credit) \
                            >= Decimal(invoice_object.total_cost):
                        raise api_exceptions.Conflict409(
                            _(
                                "There is no need for a hybrid payment. "
                                "Credit is already enough!",
                            )
                        )
                    attrs['total_cost'] = Tools.make_safe_payment_amount(
                        abs(
                            Decimal(
                                invoice_object.subscription.customer.credit,
                            ) - Decimal(
                                invoice_object.total_cost,
                            )
                        ),
                    )
                else:
                    attrs['total_cost'] = invoice_object.total_cost
                if invoice_object.status_code == \
                        FinanceConfigurations.Invoice.STATE_CHOICES[2][0]:
                    raise api_exceptions.Conflict409(conflict_message_payed)
                if invoice_object.status_code == \
                        FinanceConfigurations.Invoice.STATE_CHOICES[3][0]:
                    raise api_exceptions.Conflict409(conflict_message_revoked)
            except invoice_class.DoesNotExist:
                raise api_exceptions.NotFound404(
                    f"{attrs['used_for_id']} "
                    f"{ErrorMessages.GENERIC_404}"
                )
        else:
            if Decimal(attrs['total_cost']) <= Decimal(0):
                raise serializers.ValidationError(
                    {
                        "total_cost": _("Can not be empty or less than zero")
                    }
                )
            attrs['total_cost'] = Tools.make_safe_payment_amount(
                attrs['total_cost'],
            )

        attrs.pop("is_hybrid")

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
        validated_data['updated_status_at'] = datetime.now()
        validated_data['tracking_code'] = uuid.uuid4()
        validated_data['paid_at'] = None
        validated_data['customer_id'] = \
            self.initial_data['customer_id']

        if 'subscription_code' in validated_data:
            validated_data.pop('subscription_code')

        return CreditInvoice.objects.create(**validated_data)


class CreditInvoicesSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    subscription_code = serializers.CharField(required=False)

    class Meta:
        model = CreditInvoice
        fields = [
            'id',
            'prime_code',
            'customer_code',
            'subscription_code',
            'number',
            'tracking_code',
            'operation_type',
            'used_for',
            'status_code',
            'created_at',
            'updated_status_at',
            'total_cost',
            'paid_at',
        ]


class CreditInvoiceExportSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            _('id'): Tools.to_string_for_export(
                instance.id,
            ),
            _('prime code'): Tools.to_string_for_export(
                instance.prime_code,
            ),
            _('tracking code'): Tools.to_string_for_export(
                instance.tracking_code,
            ),
            _('subscription code'): Tools.to_string_for_export(
                instance.subscription_code,
            ),
            _('number'): Tools.to_string_for_export(
                instance.number,
            ),
            _('status code'): Tools.to_string_for_export(
                instance.status_label,
            ),
            _('used for'): Tools.to_string_for_export(
                Tools.translator(instance.used_for),
            ),
            _('used for id'): Tools.to_string_for_export(
                instance.used_for_id,
            ),
            _('operation type'): Tools.to_string_for_export(
                Tools.translator(instance.operation_type),
            ),
            _('total cost'): Tools.to_string_for_export(
                instance.total_cost,
            ),
            _('description'): Tools.to_string_for_export(
                instance.description,
            ),
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
        model = CreditInvoice


class IncreaseCreditSerializer(serializers.Serializer):
    credit = serializers.DecimalField(
        required=True,
        decimal_places=2,
        max_digits=20,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
