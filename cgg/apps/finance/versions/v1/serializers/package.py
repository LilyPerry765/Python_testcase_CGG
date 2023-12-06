from datetime import datetime
from decimal import Decimal, ROUND_CEILING

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from cgg.apps.finance.models import Package
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.services.tax import TaxService
from cgg.core.error_messages import ErrorMessages


def get_price(value, discount):
    assert 0 <= discount < 100
    tax_percent = TaxService.get_tax_percent()
    tax_cost = (value * Decimal(tax_percent)) / Decimal(100)
    price_with_tax = Decimal(tax_cost + value).to_integral_exact(
        rounding=ROUND_CEILING
    )
    package_discount = Decimal((price_with_tax * discount) / 100)
    package_price = price_with_tax - package_discount

    if package_price < Decimal(0):
        package_price = Decimal(0)

    return price_with_tax, package_price


def generate_package_code():
    prefix = settings.CGG['PACKAGE_CODE_PREFIX']
    try:
        latest_generated = Package.objects.filter(
            package_code__icontains=prefix,
        ).latest('created_at')
    except Package.DoesNotExist:
        latest_generated = None

    if latest_generated:
        number = str(int(
            latest_generated.package_code.strip(prefix)
        ) + 1).zfill(5)
    else:
        number = str(1).zfill(5)

    return f"{prefix}{number}"


class PackageMiniSerializer(serializers.ModelSerializer):
    package_price = serializers.DecimalField(
        read_only=True,
        max_digits=20,
        decimal_places=2,
    )
    package_pure_price = serializers.DecimalField(
        read_only=True,
        max_digits=20,
        decimal_places=2,
    )
    package_discount = serializers.IntegerField(
        min_value=0,
        max_value=99,
    )
    package_value = serializers.DecimalField(
        required=True,
        max_digits=20,
        decimal_places=2,
        min_value=100,
    )
    package_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    package_name = serializers.CharField(required=True)

    class Meta:
        model = Package
        fields = [
            'id',
            'package_code',
            'package_name',
            'package_price',
            'package_pure_price',
            'package_discount',
            'package_value',
        ]
        read_only_fields = (
            'id',
            'package_code',
            'package_name',
            'package_price',
            'package_pure_price',
            'package_discount',
            'package_value',
        )


class PackageSerializer(serializers.ModelSerializer):
    package_price = serializers.DecimalField(
        read_only=True,
        max_digits=20,
        decimal_places=2,
    )
    package_pure_price = serializers.DecimalField(
        read_only=True,
        max_digits=20,
        decimal_places=2,
    )
    package_discount = serializers.IntegerField(
        default=0,
        min_value=0,
        max_value=99,
    )
    package_value = serializers.DecimalField(
        required=True,
        max_digits=20,
        decimal_places=2,
        min_value=100,
    )
    package_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    package_name = serializers.CharField(required=True)
    is_active = serializers.BooleanField(required=False)
    is_featured = serializers.BooleanField(required=False)
    start_at = serializers.CharField(required=False)
    end_at = serializers.CharField(required=False)
    package_due = serializers.ChoiceField(
        required=True,
        choices=[
            FinanceConfigurations.Package.TYPES[0][0],
            FinanceConfigurations.Package.TYPES[1][0],
            FinanceConfigurations.Package.TYPES[2][0],
            FinanceConfigurations.Package.TYPES[3][0],
            FinanceConfigurations.Package.TYPES[4][0],
            FinanceConfigurations.Package.TYPES[5][0],
            FinanceConfigurations.Package.TYPES[6][0],
            FinanceConfigurations.Package.TYPES[7][0],
            FinanceConfigurations.Package.TYPES[8][0],
            FinanceConfigurations.Package.TYPES[9][0],
            FinanceConfigurations.Package.TYPES[10][0],
            FinanceConfigurations.Package.TYPES[11][0],
        ],
    )

    class Meta:
        model = Package
        fields = [
            'id',
            'package_code',
            'package_name',
            'package_due',
            'package_discount',
            'package_price',
            'package_pure_price',
            'package_value',
            'is_active',
            'is_featured',
            'start_at',
            'end_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = (
            'id',
            'package_price',
            'package_pure_price',
            'created_at',
            'updated_at',
        )

    def update(self, instance, validated_data):
        if 'package_due' in validated_data:
            validated_data.pop('package_due')
        if 'package_code' in validated_data:
            validated_data.pop('package_code')
        if 'package_price' in validated_data:
            validated_data.pop('package_price')
        if 'package_discount' not in validated_data:
            validated_data['package_discount'] = 0
        if 'package_value' in validated_data:
            package_value = Decimal(validated_data['package_value'])
            validated_data['package_pure_price'], validated_data[
                'package_price'] = get_price(
                package_value,
                validated_data['package_discount'],
            )

        return super().update(instance, validated_data)

    def create(self, validated_data):
        if ('package_code' not in validated_data) or (
                'package_code' in validated_data and
                not validated_data['package_code']
        ):
            validated_data['package_code'] = generate_package_code()
        package_value = Decimal(validated_data['package_value'])
        if 'package_discount' not in validated_data:
            validated_data['package_discount'] = 0
        validated_data['package_pure_price'], validated_data[
            'package_price'] = get_price(
            package_value,
            validated_data['package_discount'],
        )
        validated_data['package_code'] = str(
            validated_data['package_code']
        ).lower()

        if Package.objects.filter(
                package_code=validated_data['package_code'],
        ).count() > 0:
            raise serializers.ValidationError({
                'package_code': _("This code is exists, choose another")
            })

        return super().create(validated_data)

    def validate(self, attrs):
        if 'start_at' in attrs:
            try:
                attrs['start_at'] = datetime.fromtimestamp(float(
                    attrs['start_at'],
                ))
            except Exception:
                raise serializers.ValidationError({
                    'start_at': ErrorMessages.PACKAGE_START_DATE_400,
                })
        if 'end_at' in attrs:
            try:
                attrs['end_at'] = datetime.fromtimestamp(float(
                    attrs['end_at'],
                ))
            except Exception:
                raise serializers.ValidationError({
                    'end_at': ErrorMessages.PACKAGE_END_DATE_400,
                })
        if 'end_at' in attrs and 'start_at' in attrs:
            if attrs['start_at'] >= attrs['end_at']:
                raise serializers.ValidationError({
                    'start_at': ErrorMessages.PACKAGE_START_DATE_GREATER_400,
                })

        return attrs
