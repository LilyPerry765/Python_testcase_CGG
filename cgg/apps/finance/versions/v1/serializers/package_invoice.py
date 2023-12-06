import uuid
from datetime import datetime

from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Package, PackageInvoice
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.package import (
    PackageMiniSerializer,
)
from cgg.core.tools import Tools


class PackageInvoiceSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(
        read_only=True,
        max_digits=20,
        decimal_places=2,
    )
    subscription_code = serializers.CharField(required=False)
    auto_renew = serializers.BooleanField(required=False)
    credit_invoice_id = serializers.CharField(required=False)
    package_id = serializers.CharField(required=True)
    package = PackageMiniSerializer(
        required=False,
        read_only=True,
    )

    class Meta:
        model = PackageInvoice
        fields = [
            'id',
            'prime_code',
            'subscription_code',
            'number',
            'credit_invoice_id',
            'tracking_code',
            'status_code',
            'package_id',
            'total_cost',
            'total_value',
            'expired_value',
            'is_active',
            'is_expired',
            'auto_renew',
            'expired_at',
            'description',
            'package',
            'created_at',
            'updated_status_at',
            'paid_at',
        ]
        read_only_fields = (
            'id',
            'prime_code',
            'credit_invoice_id',
            'package_id',
            'is_active',
            'is_expired',
            'auto_renew',
            'expired_at',
            'expired_value',
            'total_value',
            'package',
            'created_at',
            'updated_at',
            'updated_status_at',
            'status_code',
            'tracking_code',
        )

    def update(self, instance, validated_data):
        if instance.expired_at and instance.expired_at <= \
                datetime.now():
            raise serializers.ValidationError({
                'auto_renew': _("Can not update an expired invoice")
            })
        if instance.status_code == \
                FinanceConfigurations.Invoice.STATE_CHOICES[3][0]:
            raise serializers.ValidationError({
                'auto_renew': _("Can not update a revoked invoice")
            })
        if 'auto_renew' in validated_data:
            only_auto_renew = {
                'auto_renew': validated_data['auto_renew'],
            }
        else:
            only_auto_renew = {}

        return super().update(instance, only_auto_renew)

    def create(self, validated_data):
        package_id = Tools.uuid_validation(validated_data['package_id'])
        try:
            package_object = Package.objects.get(
                Q(
                    start_at__gte=datetime.now(),
                    end_at__lte=datetime.now(),
                ) |
                Q(
                    start_at__isnull=True,
                    end_at__lte=datetime.now(),
                ) |
                Q(
                    start_at__gte=datetime.now(),
                    end_at__isnull=True,
                )
                |
                Q(
                    start_at__isnull=True,
                    end_at__isnull=True,
                ),
                id=package_id,
                is_active=True,
            )
        except Package.DoesNotExist:
            raise serializers.ValidationError({
                'package_id': _("The package does not exists")
            })
        validated_data['status_code'] = \
            FinanceConfigurations.Invoice.STATE_CHOICES[0][0]
        validated_data['updated_status_at'] = datetime.now()
        validated_data['tracking_code'] = uuid.uuid4()
        validated_data['paid_at'] = None
        validated_data['total_cost'] = package_object.package_price
        validated_data['total_value'] = package_object.package_value
        validated_data['package'] = package_object
        validated_data['subscription_id'] = \
            self.initial_data['subscription_id']
        validated_data.pop("package_id")

        if 'subscription_code' in validated_data:
            validated_data.pop('subscription_code')

        return PackageInvoice.objects.create(**validated_data)


class PackageInvoicesSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(max_digits=20, decimal_places=2)
    subscription_code = serializers.CharField(required=False)
    package = PackageMiniSerializer(
        required=False,
        read_only=True,
    )

    class Meta:
        model = PackageInvoice
        fields = [
            'id',
            'prime_code',
            'subscription_code',
            'number',
            'tracking_code',
            'package',
            'status_code',
            'is_expired',
            'is_active',
            'expired_value',
            'total_cost',
            'total_value',
            'auto_renew',
            'expired_at',
            'created_at',
            'updated_status_at',
            'paid_at',
        ]


class PackageInvoiceExportSerializer(serializers.ModelSerializer):
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
            _('credit invoice id'): Tools.to_string_for_export(
                instance.credit_invoice_id,
            ),
            _('status code'): Tools.to_string_for_export(
                instance.status_label,
            ),
            _('package id'): Tools.to_string_for_export(
                instance.package_id,
            ),
            _('total cost'): Tools.to_string_for_export(
                instance.total_cost,
            ),
            _('total value'): Tools.to_string_for_export(
                instance.total_value,
            ),
            _('expired value'): Tools.to_string_for_export(
                instance.expired_value,
            ),
            _('is active'): Tools.to_string_for_export(
                instance.is_active,
                is_boolean=True,
            ),
            _('is expired'): Tools.to_string_for_export(
                instance.is_expired,
                is_boolean=True,
            ),
            _('auto renew'): Tools.to_string_for_export(
                instance.auto_renew,
                is_boolean=True,
            ),
            _('expired at'): Tools.to_string_for_export(
                instance.expired_at,
                is_boolean=True,
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
        model = PackageInvoice
