# --------------------------------------------------------------------------
# All models must implement BaseModel to have checksum field, this is
# critical to maintain data integrity. All Invoice type models must implement
# BaseInvoice model.
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - models.py
# Created at 2020-5-3,  11:4:42
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import re
import uuid
from datetime import datetime
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import JSONField
from django.utils.translation import gettext as _

from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core.cache import Cache
from cgg.core.integrity import Integrity


class BaseModel(models.Model):
    checksum = models.CharField(
        null=True,
        blank=True,
        max_length=512,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.checksum = Integrity.checksum(self)
        super(BaseModel, self).save(*args, **kwargs)

    @classmethod
    def model_field_exists(cls, field):
        try:
            cls._meta.get_field(field)
            return True
        except models.FieldDoesNotExist:
            return False


class Package(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    package_code = models.CharField(
        null=False,
        blank=False,
        unique=True,
        max_length=256,
        db_index=True,
    )
    package_name = models.CharField(
        null=False,
        blank=False,
        max_length=512,
    )
    package_due = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.Package.TYPES[0][0],
        max_length=64,
        choices=FinanceConfigurations.Package.TYPES,
        db_index=True,
    )
    package_discount = models.IntegerField(
        null=False,
        blank=False,
        default=0,
    )
    package_pure_price = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    package_price = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    package_value = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    start_at = models.DateTimeField(null=True, default=None)
    end_at = models.DateTimeField(null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class Destination(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    prefix = models.CharField(
        null=False,
        blank=False,
        max_length=256,
        unique=True,
    )
    name = models.CharField(null=False, blank=False, max_length=256)
    country_code = models.CharField(
        null=False,
        blank=False,
        max_length=256,
        db_index=True,
    )
    code = models.CharField(
        null=False,
        blank=False,
        max_length=256,
        choices=FinanceConfigurations.Destination.CODE_CHOICES,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.country_code} - {self.code} - {self.name}:" \
               f" {self.prefix}"


class Branch(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    branch_code = models.CharField(
        unique=True,
        max_length=256,
        null=False,
        blank=False,
        db_index=True,
    )
    branch_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )
    destinations = models.ManyToManyField(
        Destination,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Branches"


class Operator(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    operator_code = models.CharField(
        unique=True,
        max_length=256,
        null=False,
        blank=False,
        db_index=True,
    )
    destinations = models.ManyToManyField(
        Destination,
        blank=True,
    )
    inbound_rate = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    outbound_rate = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    rate_time_type = models.CharField(
        max_length=128,
        null=False,
        blank=False,
        choices=FinanceConfigurations.Profit.RATE_TIME_TYPE,
        default=FinanceConfigurations.Profit.RATE_TIME_TYPE[0][0],
    )
    rate_time = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MaxValueValidator(60),
            MinValueValidator(1)
        ],
        default=60
    )
    inbound_divide_on_percent = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MaxValueValidator(99),
            MinValueValidator(1)
        ],
        default=80
    )
    outbound_divide_on_percent = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MaxValueValidator(99),
            MinValueValidator(1)
        ],
        default=80
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.operator_code}"


class Profit(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    operator = models.ForeignKey(
        Operator,
        related_name='profits',
        on_delete=models.SET_NULL,
        null=True,
    )
    inbound_used_percent = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MaxValueValidator(99),
            MinValueValidator(1)
        ],
        default=80
    )
    outbound_used_percent = models.IntegerField(
        null=False,
        blank=False,
        validators=[
            MaxValueValidator(99),
            MinValueValidator(1)
        ],
        default=80
    )
    inbound_usage = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    outbound_usage = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    inbound_cost_first_part = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    inbound_cost_second_part = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    outbound_cost_first_part = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    outbound_cost_second_part = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    status_code = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.Profit.STATE_CHOICES[0][0],
        max_length=64,
        choices=FinanceConfigurations.Profit.STATE_CHOICES,
        db_index=True,
    )
    from_date = models.DateTimeField()
    to_date = models.DateTimeField()
    updated_status_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def operator_code(self):
        return self.operator.operator_code

    @property
    def total_cost_inbound(self):
        return self.inbound_cost_first_part + self.inbound_cost_second_part

    @property
    def total_cost_outbound(self):
        return self.outbound_cost_first_part + self.outbound_cost_second_part

    @property
    def total_usage(self):
        return self.inbound_usage + self.outbound_usage


class Customer(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # This becomes customer's ID from trunk
    customer_code = models.CharField(
        unique=True,
        max_length=256,
        null=False,
        blank=False,
        db_index=True,
    )
    credit = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def prime_code(self):
        return "{}-{}".format(
            "prime",
            str(self.customer_code).zfill(6),
        )


class Subscription(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    customer = models.ForeignKey(
        Customer,
        related_name='subscriptions',
        on_delete=models.PROTECT,
    )
    branch = models.ForeignKey(
        Branch,
        related_name='subscriptions',
        on_delete=models.SET_NULL,
        null=True,
    )
    subscription_code = models.CharField(
        unique=True,
        max_length=256,
        null=False,
        blank=False,
        db_index=True,
    )
    subscription_type = models.CharField(
        max_length=128,
        null=False,
        blank=False,
        choices=FinanceConfigurations.Subscription.TYPE,
        default=FinanceConfigurations.Subscription.TYPE[0][0],
        db_index=True,
    )
    number = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        db_index=True,
    )
    auto_pay = models.BooleanField(default=True)
    is_allocated = models.BooleanField(default=True, db_index=True)
    deallocated_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    deallocation_cause = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        choices=FinanceConfigurations.Subscription.DEALLOCATION_CAUSE,
        db_index=True,
    )
    deallocate_warned = models.BooleanField(default=False, db_index=True)
    # Last successful pay on interim or periodic invoice
    latest_paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    # Is requested an interim invoice recently
    interim_request = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def interim_requested(self):
        self.interim_request = True
        self.save()

    def interim_processed(self):
        self.interim_request = False
        self.save()

    def deallocate(self, cause):
        assert cause in (
            FinanceConfigurations.Subscription.DEALLOCATION_CAUSE[0][0],
            FinanceConfigurations.Subscription.DEALLOCATION_CAUSE[1][0],
        )
        self.is_allocated = False
        self.deallocated_at = datetime.now()
        self.deallocation_cause = cause
        self.save()
        with(open('khosro_logs.txt','s')) as f:
            f.write('deallocated suucessfuly')
            f.write('\n')

    def update_latest_payed(self):
        self.latest_paid_at = datetime.now()
        self.save()

    @property
    def credit(self):
        return self.customer.credit

    @property
    def prime_code(self):
        return self.customer.prime_code

    @property
    def customer_code(self):
        return self.customer.customer_code


class BaseInvoice(BaseModel):
    """
    Base class for all type of invoices
    total_cost must be implemented
    """
    status_code = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.Invoice.STATE_CHOICES[0][0],
        max_length=64,
        choices=FinanceConfigurations.Invoice.STATE_CHOICES,
        db_index=True,
    )
    total_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_status_at = models.DateTimeField()
    pay_cool_down = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        abstract = True

    @property
    def status_label(self):
        return dict(FinanceConfigurations.Invoice.STATE_CHOICES).get(
            self.status_code,
        )


class CreditInvoice(BaseInvoice):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tracking_code = models.UUIDField(default=uuid.uuid4, db_index=True)
    customer = models.ForeignKey(
        Customer,
        related_name='credit_invoices',
        on_delete=models.PROTECT,
    )
    operation_type = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
        max_length=64,
        choices=FinanceConfigurations.CreditInvoice.OPERATION_TYPES,
        db_index=True,
    )
    used_for = models.CharField(
        null=True,
        blank=True,
        default=None,
        max_length=128,
        choices=FinanceConfigurations.CreditInvoice.USED_FOR,
    )
    used_for_id = models.UUIDField(
        null=True,
        blank=True,
        default=None,
    )
    description = models.TextField(blank=True)

    @property
    def prime_code(self):
        return self.customer.prime_code

    @property
    def customer_code(self):
        return self.customer.customer_code

    @property
    def subscription(self):
        if self.used_for:
            if self.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                invoice_class = Invoice
            elif self.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                invoice_class = BaseBalanceInvoice
            else:
                invoice_class = PackageInvoice
            try:
                invoice_object = invoice_class.objects.get(
                    id=self.used_for_id
                )
                return invoice_object.subscription
            except invoice_class.DoesNotExist:
                pass

        return None

    @property
    def related_tracking_code(self):
        if self.used_for:
            if self.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                invoice_class = Invoice
            elif self.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                invoice_class = BaseBalanceInvoice
            else:
                invoice_class = PackageInvoice
            try:
                invoice_object = invoice_class.objects.get(
                    id=self.used_for_id
                )
                return invoice_object.tracking_code
            except invoice_class.DoesNotExist:
                pass

        return None

    @property
    def subscription_code(self):
        if self.subscription:
            return self.subscription.subscription_code

        return None

    @property
    def number(self):
        if self.subscription:
            return self.subscription.number

        return None


class Invoice(BaseInvoice):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tracking_code = models.UUIDField(default=uuid.uuid4, db_index=True)
    subscription = models.ForeignKey(
        Subscription,
        related_name='invoices',
        on_delete=models.PROTECT,
    )
    period_count = models.IntegerField(null=False, blank=False)
    tax_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    tax_percent = models.IntegerField(null=False, blank=False)
    discount = models.DecimalField(
        null=False,
        blank=False,
        default=Decimal(0),
        max_digits=20,
        decimal_places=2,
    )
    discount_description = models.CharField(
        null=True,
        blank=True,
        default='',
        max_length=512,
    )
    debt = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    subscription_fee = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    # Postpaid part of invoice
    landlines_long_distance_usage = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=Decimal(0),
    )
    landlines_long_distance_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=Decimal(0),
    )
    landlines_local_usage = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    landlines_corporate_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    landlines_corporate_usage = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    landlines_local_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    mobile_usage = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    mobile_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    international_usage = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    international_cost = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    # Prepaid part of invoice
    landlines_long_distance_usage_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=Decimal(0),
    )
    landlines_long_distance_cost_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
        default=Decimal(0),
    )
    landlines_local_usage_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    landlines_corporate_cost_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    landlines_corporate_usage_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    landlines_local_cost_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    mobile_usage_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    mobile_cost_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    international_usage_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    international_cost_prepaid = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    invoice_type_code = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.Invoice.TYPES[0][0],
        max_length=64,
        choices=FinanceConfigurations.Invoice.TYPES,
    )
    from_date = models.DateTimeField()
    to_date = models.DateTimeField()
    due_date = models.DateTimeField(null=True, blank=True)
    due_date_notified = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.Invoice.DUE_DATE_NOTIFY[0][0],
        max_length=64,
        choices=FinanceConfigurations.Invoice.DUE_DATE_NOTIFY,
        db_index=True,
    )
    description = models.TextField(blank=True)
    credit_invoice = models.OneToOneField(
        CreditInvoice,
        related_name='invoice',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    on_demand = models.BooleanField(default=False)

    @property
    def total_usage_cost_prepaid(self):
        return self.landlines_local_cost_prepaid + \
               self.landlines_long_distance_cost_prepaid + \
               self.mobile_cost_prepaid + self.international_cost_prepaid + \
               self.landlines_corporate_cost_prepaid

    @property
    def total_usage_cost_postpaid(self):
        return self.landlines_local_cost + self.mobile_cost + \
               self.landlines_long_distance_cost + self.international_cost + \
               self.landlines_corporate_cost

    @property
    def total_usage_cost(self):
        return self.total_usage_cost_prepaid + self.total_usage_cost_postpaid

    @property
    def total_usage_prepaid(self):
        return self.landlines_local_usage_prepaid + \
               self.landlines_long_distance_usage_prepaid + \
               self.mobile_usage_prepaid + self.international_usage_prepaid \
               + self.landlines_corporate_usage_prepaid

    @property
    def total_usage_postpaid(self):
        return self.landlines_local_usage + \
               self.landlines_long_distance_usage + self.mobile_usage + \
               self.international_usage + self.landlines_corporate_usage

    @property
    def total_usage(self):
        return self.total_usage_postpaid + self.total_usage_prepaid

    @property
    def difference_with_rounded(self):
        return self.total_cost - self.total_cost_rounded

    @property
    def total_cost_rounded(self):
        return int(self.total_cost / 1000) * 1000

    @property
    def is_overdue(self):
        if self.due_date:
            return self.due_date < datetime.now()
        return False

    @property
    def subscription_code(self):
        return self.subscription.subscription_code

    @property
    def prime_code(self):
        return self.subscription.customer.prime_code

    @property
    def customer_code(self):
        return self.subscription.customer.customer_code

    @property
    def number(self):
        return self.subscription.number

    @property
    def invoice_type_label(self):
        return dict(FinanceConfigurations.Invoice.TYPES).get(
            self.invoice_type_code,
        )

    @property
    def credit(self):
        return float(self.subscription.credit)


class BaseBalanceInvoice(BaseInvoice):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tracking_code = models.UUIDField(default=uuid.uuid4, db_index=True)
    subscription = models.ForeignKey(
        Subscription,
        related_name='base_balance_invoices',
        on_delete=models.PROTECT,
    )
    description = models.TextField(blank=True)
    credit_invoice = models.OneToOneField(
        CreditInvoice,
        related_name='base_balance_invoice',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    operation_type = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
        max_length=64,
        choices=FinanceConfigurations.CreditInvoice.OPERATION_TYPES,
        db_index=True,
    )

    @property
    def subscription_code(self):
        return self.subscription.subscription_code

    @property
    def customer_code(self):
        return self.subscription.customer.customer_code

    @property
    def prime_code(self):
        return self.subscription.customer.prime_code

    @property
    def number(self):
        return self.subscription.number


class PackageInvoice(BaseInvoice):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tracking_code = models.UUIDField(default=uuid.uuid4, db_index=True)
    subscription = models.ForeignKey(
        Subscription,
        related_name='package_invoices',
        on_delete=models.PROTECT,
    )
    total_value = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    expired_value = models.DecimalField(
        null=True,
        blank=True,
        max_digits=20,
        decimal_places=2,
    )
    expired_at = models.DateTimeField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    auto_renew = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False, db_index=True)
    description = models.TextField(blank=True)
    package = models.ForeignKey(
        Package,
        related_name='package_invoices',
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
    )
    credit_invoice = models.OneToOneField(
        CreditInvoice,
        related_name='package_invoice',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    @property
    def subscription_code(self):
        return self.subscription.subscription_code

    @property
    def number(self):
        return self.subscription.number

    @property
    def customer_code(self):
        return self.subscription.customer.customer_code

    @property
    def prime_code(self):
        return self.subscription.customer.prime_code


class Payment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    credit_invoice = models.ForeignKey(
        CreditInvoice,
        related_name='payments',
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        null=False,
        blank=False,
        max_digits=20,
        decimal_places=2,
    )
    status_code = models.CharField(
        null=False,
        blank=False,
        default=FinanceConfigurations.Payment.STATE_CHOICES[0][0],
        max_length=64,
        choices=FinanceConfigurations.Payment.STATE_CHOICES,
        db_index=True,
    )
    gateway = models.CharField(null=True, blank=False, max_length=512)
    extra_data = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_status_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def status_label(self):
        return dict(FinanceConfigurations.Payment.STATE_CHOICES).get(
            self.status_code,
        )

    @property
    def prime_code(self):
        return self.credit_invoice.customer.prime_code

    @property
    def customer_code(self):
        return self.credit_invoice.customer.customer_code

    @property
    def subscription_code(self):
        return self.credit_invoice.subscription_code

    @property
    def number(self):
        return self.credit_invoice.number

    @property
    def used_for(self):
        if self.credit_invoice.used_for:
            return self.credit_invoice.used_for

        return 'credit_invoice'

    @property
    def related_tracking_code(self):
        if self.credit_invoice.used_for:
            return self.credit_invoice.related_tracking_code
        return self.credit_invoice.tracking_code


class Attachment(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    file_id = models.CharField(null=True, blank=False, max_length=512)
    payment = models.ForeignKey(
        Payment,
        related_name='attachments',
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class Tax(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    country_code = models.CharField(
        null=False,
        blank=False,
        max_length=256,
        unique=True,
        db_index=True,
    )
    tax_percent = models.IntegerField(null=False, blank=False)


class RuntimeConfig(BaseModel):
    item_key = models.CharField(
        null=False,
        blank=False,
        unique=True,
        max_length=512,
        choices=FinanceConfigurations.RuntimeConfig.KEY_CHOICES,
        db_index=True,
    )
    item_value = models.CharField(null=False, blank=False, max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def delete(self, using=None, keep_parents=False):
        """
        Prevent deleting any RuntimeConfig
        :param using:
        :param keep_parents:
        :return:
        """
        pass

    def save(self, *args, **kwargs):
        if self.item_key in (
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[2][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[3][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[7][0],
        ):
            prefixes = list(
                filter(
                    None,
                    [x.strip() if re.match(
                        re.compile(r'^\+?\d+(?:,\d*)?$'), x.strip()
                    ) else '' for x in self.item_value.strip().split(',''')],
                )
            )
            self.item_value = ",".join(prefixes)

        if self.item_key in (
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[0][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[1][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[4][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[5][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[6][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[8][0],
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[9][0],
        ):
            try:
                value = int(self.item_value)
            except ValueError:
                value = 0
            if value < 0:
                value = 0
            self.item_value = value

        Cache.delete(
            key=Cache.KEY_CONVENTIONS['runtime_config'],
            values={
                'key': self.item_key,
            },
        )

        super(RuntimeConfig, self).save(*args, **kwargs)


class FailedJob(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    job_title = models.CharField(
        null=True,
        blank=False,
        max_length=512,
        choices=FinanceConfigurations.Jobs.TYPES,
    )
    service_version = models.CharField(
        null=True,
        blank=False,
        max_length=512,
        default='v1',
        choices=(
            ('v1', _('Version 1')),
        ),
    )
    service_name = models.CharField(null=False, blank=False, max_length=512)
    method_name = models.CharField(null=False, blank=False, max_length=512)
    method_args = JSONField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    error_message = models.CharField(null=False, blank=False, max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class CommandRun(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    command_title = models.CharField(
        null=True,
        blank=False,
        max_length=512,
        choices=FinanceConfigurations.Commands.TYPES,
        default=FinanceConfigurations.Commands.TYPES[0][0]
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
