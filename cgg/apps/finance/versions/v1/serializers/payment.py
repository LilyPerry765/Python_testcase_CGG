from datetime import datetime

from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from cgg.apps.finance.models import (
    BaseBalanceInvoice,
    CreditInvoice,
    Invoice,
    PackageInvoice,
    Payment,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.attachment import (
    AttachmentSerializer,
)
from cgg.apps.finance.versions.v1.services.attachment import (
    AttachmentService,
)
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.tools import Tools


class MigratePaymentsSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
    )
    status_code = serializers.CharField()
    gateway = serializers.CharField()
    extra_data = serializers.JSONField()
    created_at = serializers.DateTimeField(required=True)
    updated_at = serializers.DateTimeField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PaymentSerializer(serializers.ModelSerializer):
    # files is an on-fly field to fill attachments
    files = serializers.ListField(required=False)
    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
    )
    attachments = AttachmentSerializer(many=True, required=False)
    credit_invoice_id = serializers.CharField(required=True)
    credit_invoice_tracking_code = serializers.CharField(required=False)
    customer_code = serializers.CharField(required=False)
    prime_code = serializers.CharField(required=False)
    gateway = serializers.CharField()
    used_for = serializers.CharField(required=False)

    class Meta:
        model = Payment
        fields = [
            'id',
            'credit_invoice_id',
            'credit_invoice_tracking_code',
            'prime_code',
            'customer_code',
            'subscription_code',
            'number',
            'amount',
            'status_code',
            'credit_invoice_id',
            'used_for',
            'gateway',
            'attachments',
            'created_at',
            'updated_at',
            'updated_status_at',
            'extra_data',
            'files',
        ]
        read_only_fields = (
            'id',
            'amount',
            'credit_invoice_id',
            'credit_invoice_tracking_code',
            'created_at',
            'updated_at',
            'updated_status_at',
            'payment_type',
            'prime_code',
            'customer_code',
            'subscription_code',
            'number',
            'credit_invoice_id',
            'used_for',
            'files',
        )

    def update(self, instance, validated_data):
        if 'status_code' in validated_data:
            if instance.status_code == validated_data['status_code']:
                raise ValidationError({
                    'status_code': _(
                        "Current state and requested one are the same",
                    )
                }
                )
            elif instance.status_code == \
                    FinanceConfigurations.Payment.STATE_CHOICES[0][0]:
                instance.status_code = validated_data['status_code']
                instance.updated_status_at = datetime.now()
                # Pop everything except status_code and extra_data
                if 'amount' in validated_data:
                    validated_data.pop('amount')

                if 'credit_invoice_id' in validated_data:
                    validated_data.pop('credit_invoice')

                if 'gateway' in validated_data:
                    validated_data.pop('gateway')

                return super().update(instance, validated_data)
            else:
                raise ValidationError({
                    'status_code': _(
                        "Can't change from current state")
                }
                )

        raise ValidationError({
            'non_fields': _("Only 'status_code' and 'extra_data' can be "
                            "updated")
        }
        )

    def create(self, validated_data):
        uuid = Tools.uuid_validation(validated_data['credit_invoice_id'])
        try:
            credit_object = CreditInvoice.objects.get(
                id=uuid
            )
        except CreditInvoice.DoesNotExist:
            raise api_exceptions.NotFound404(
                f"{validated_data['credit_invoice_id']} "
                f"{ErrorMessages.CREDIT_INVOICE_404}"
            )
        # Check for status_code of credit invoice
        if credit_object.status_code != \
                FinanceConfigurations.Invoice.STATE_CHOICES[0][0]:
            conflict_message = _("This credit invoice is revoked")
            if credit_object.status_code == \
                    FinanceConfigurations.Invoice.STATE_CHOICES[1][0]:
                conflict_message = _(
                    "This credit invoice has a pending payment",
                )
            if credit_object.status_code == \
                    FinanceConfigurations.Invoice.STATE_CHOICES[2][0]:
                conflict_message = _("This credit invoice is already payed")

            raise api_exceptions.Conflict409(conflict_message)

        validated_data['amount'] = credit_object.total_cost
        validated_data['credit_invoice_id'] = credit_object.id

        if validated_data['gateway'] == FinanceConfigurations.Payment.OFFLINE:
            if "files" not in validated_data or not validated_data['files']:
                raise api_exceptions.ValidationError400(
                    {
                        "files": _(
                            "Can not create an offline payment without "
                            "attachments",
                        )
                    }
                )
            if credit_object.used_for:
                raise api_exceptions.Conflict409(
                    _("Offline payment only can be used for credit invoices")
                )
            credit_object.status_code = \
                FinanceConfigurations.Invoice.STATE_CHOICES[1][0]
            credit_object.save()

        validated_data['status_code'] = \
            FinanceConfigurations.Payment.STATE_CHOICES[0][0]

        files = None
        if 'files' in validated_data:
            files = validated_data.pop('files')

        # Cool down checking
        if validated_data['gateway'] not in (
                FinanceConfigurations.Payment.OFFLINE,
        ):
            if credit_object.used_for:
                if credit_object.used_for == \
                        FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                    invoice_class = Invoice
                elif credit_object.used_for == \
                        FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                    invoice_class = BaseBalanceInvoice
                else:
                    invoice_class = PackageInvoice
                try:
                    related_invoice = invoice_class.objects.get(
                        id=credit_object.used_for_id
                    )
                except invoice_class.DoesNotExist:
                    raise api_exceptions.NotFound404(
                        f"{validated_data['used_for_id']} "
                        f"{ErrorMessages.GENERIC_404}"
                    )
                if related_invoice.pay_cool_down is not None and \
                        datetime.now() < related_invoice.pay_cool_down:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.PAYMENT_409_COOL_DOWN,
                    )
                else:
                    related_invoice.pay_cool_down = \
                        CommonService.payment_cool_time()
                    related_invoice.save()
            else:
                if credit_object.pay_cool_down is not None and \
                        datetime.now() < credit_object.pay_cool_down:
                    raise api_exceptions.Conflict409(
                        ErrorMessages.PAYMENT_409_COOL_DOWN,
                    )
                else:
                    credit_object.pay_cool_down = \
                        CommonService.payment_cool_time()
                    credit_object.save()

        payment_object = Payment.objects.create(**validated_data)
        if files and validated_data['gateway'] == \
                FinanceConfigurations.Payment.OFFLINE:
            for file_id in files:
                payment_object.attachments.add(
                    AttachmentService.create_attachment(file_id)
                )

        return payment_object

    def to_representation(self, instance):
        return_data = super(PaymentSerializer, self).to_representation(
            instance,
        )

        if "files" in return_data:
            return_data.pop("files")

        return return_data


class PaymentsSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    credit_invoice_id = serializers.CharField(required=False)
    related_tracking_code = serializers.CharField(required=False)

    class Meta:
        model = Payment
        fields = [
            'id',
            'prime_code',
            'credit_invoice_id',
            'related_tracking_code',
            'customer_code',
            'subscription_code',
            'number',
            'gateway',
            'used_for',
            'amount',
            'status_code',
            'credit_invoice_id',
            'updated_status_at',
            'created_at',
        ]


class PaymentExportSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return {
            _('id'): Tools.to_string_for_export(
                instance.id,
            ),
            _('related tracking code'): Tools.to_string_for_export(
                instance.related_tracking_code,
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
            _('amount'): Tools.to_string_for_export(
                instance.amount,
            ),
            _('status code'): Tools.to_string_for_export(
                instance.status_label,
            ),
            _('credit invoice id'): Tools.to_string_for_export(
                instance.credit_invoice_id,
            ),
            _('used for'): Tools.to_string_for_export(
                Tools.translator(instance.used_for),
            ),
            _('gateway'): Tools.to_string_for_export(
                instance.gateway,
            ),
            _('created at'): Tools.to_jalali_date(
                instance.created_at,
            ),
            _('updated at'): Tools.to_jalali_date(
                instance.updated_at,
            ),
            _('updated status at'): Tools.to_jalali_date(
                instance.updated_status_at,
            ),
        }

    class Meta:
        model = Payment
