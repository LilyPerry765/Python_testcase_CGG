import json

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from rangefilter.filter import DateRangeFilter

from cgg.apps.finance.models import (
    Attachment,
    BaseBalanceInvoice,
    Branch,
    CommandRun,
    CreditInvoice,
    Customer,
    Destination,
    FailedJob,
    Invoice,
    Operator,
    Package,
    PackageInvoice,
    Payment,
    Profit,
    RuntimeConfig,
    Subscription,
    Tax,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.destination import (
    DestinationSerializer,
)
from cgg.apps.finance.versions.v1.serializers.package import PackageSerializer
from cgg.apps.finance.versions.v1.services.branch import BranchService
from cgg.apps.finance.versions.v1.services.destination import (
    DestinationService,
)
from cgg.apps.finance.versions.v1.services.invoice import (
    InvoiceService,
)
from cgg.apps.finance.versions.v1.services.job import JobService
from cgg.apps.finance.versions.v1.services.operator import (
    OperatorService,
)
from cgg.apps.finance.versions.v1.services.package import PackageService
from cgg.apps.finance.versions.v1.services.subscription import (
    SubscriptionService,
)
from cgg.core import api_exceptions
from cgg.core.integrity import Integrity


def check_integrity(self, request, queryset):
    """
    A common method for all models to check data integrity
    :param self:
    :param request:
    :param queryset:
    :return:
    """
    for model_object in queryset:
        if Integrity.check(
                model_object=model_object
        ):
            messages.add_message(
                request,
                messages.INFO,
                f"{model_object.id} is valid",
            )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                f"{model_object.id} is manipulated",
            )


check_integrity.short_description = _('Check integrity')


@admin.register(FailedJob)
class FailedJobAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['service_name', 'method_name']
    list_display = (
        'job_title',
        'service_version',
        'service_name',
        'method_name',
        'is_done',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'job_title',
            ),
        }),
        ('Details', {
            'classes': ('collapse',),
            'fields': (
                'service_version',
                'service_name',
                'method_name',
                'method_args',
            ),
        }),
        ('Action & errors', {
            'classes': ('collapse',),
            'fields': (
                'is_done',
                'error_message',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        'is_done',
        'service_name',
        'job_title',
        ('created_at', DateRangeFilter),
    )

    list_per_page = 20

    actions = ['do_the_job', check_integrity, ]

    def do_the_job(self, request, queryset):
        count_all = queryset.count()
        count_done = 0
        count_failed = 0

        for job_object in queryset:
            if JobService.redo_the_job(
                    job_object=job_object
            ):
                count_done += 1
            else:
                count_failed += 1

        self.message_user(
            request,
            f"{_('All Jobs:')} {count_all} - {_('Done Jobs:')} {count_done} "
            f"{_('Failed Jobs:')} {count_failed}"
        )

    do_the_job.short_description = _('Redo the job')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Profit)
class ProfitAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['branch_code', 'branch_name']
    list_display = (
        'id',
        'operator_link',
        'from_date',
        'to_date',
        'status_code',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'operator',
        'status_code',
        ('created_at', DateRangeFilter),
        ('updated_status_at', DateRangeFilter),
    )
    list_per_page = 20
    readonly_fields = [
        'id',
        'operator_link',
        'inbound_used_percent',
        'outbound_used_percent',
        'inbound_cost_first_part',
        'inbound_cost_second_part',
        'outbound_cost_first_part',
        'outbound_cost_second_part',
        'status_code',
        'from_date',
        'to_date',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'operator_link',
                'operator',
                'inbound_used_percent',
                'outbound_used_percent',
                'inbound_cost_first_part',
                'inbound_cost_second_part',
                'outbound_cost_first_part',
                'outbound_cost_second_part',
                'status_code',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'from_date',
                'to_date',
                'created_at',
                'updated_at',
                'updated_status_at',
            ),
        }),
    )
    actions = [check_integrity, ]

    def operator_link(self, obj):
        url = reverse(
            "admin:finance_operator_change",
            args=[obj.operator.id],
        )
        link = f'<a href="{url}">{obj.operator.operator_code}</a>'

        return mark_safe(link)

    operator_link.short_description = 'Operator'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['branch_code', 'branch_name']
    list_display = (
        'id',
        'operator_code',
        'inbound_rate',
        'outbound_rate',
        'inbound_divide_on_percent',
        'outbound_divide_on_percent',
        'created_at',
        'updated_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )
    list_per_page = 20
    readonly_fields = [
        'id',
        'get_prefixes',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'operator_code',
                'rate_time_type',
                'rate_time',
                'get_prefixes',
                'destinations',
                'inbound_rate',
                'outbound_rate',
                'inbound_divide_on_percent',
                'outbound_divide_on_percent',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    actions = [check_integrity, ]

    def save_model(self, request, obj, form, change):
        destination_names = []
        for prefix in form.cleaned_data['destinations']:
            destination_names.append(prefix.name)

        body = form.cleaned_data
        body.pop('destinations')
        body['destination_names'] = destination_names
        body['inbound_rate'] = str(body['inbound_rate'])
        body['outbound_rate'] = str(body['outbound_rate'])
        body = json.dumps(body)
        if change:
            try:
                OperatorService.update_operator(
                    obj.id,
                    body,
                )
            except api_exceptions.NotFound404 as e:
                self.message_user(request, e, level=messages.WARNING)
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)
        else:
            try:
                OperatorService.add_operator(body)
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)

    def delete_queryset(self, request, queryset):
        try:
            for operator in queryset:
                OperatorService.remove_operator(operator.id)
        except api_exceptions.Conflict409 as e:
            self.message_user(request, e, level=messages.WARNING)
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    def get_prefixes(self, obj):
        return ", ".join([p.prefix for p in obj.destinations.all()])

    get_prefixes.short_description = 'Prefixes'


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['branch_code', 'branch_name']
    list_display = (
        'id',
        'branch_code',
        'branch_name',
        'get_prefixes',
        'created_at',
        'updated_at',
    )
    list_per_page = 20
    readonly_fields = [
        'id',
        'get_prefixes',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'branch_code',
                'branch_name',
                'get_prefixes',
                'destinations',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    actions = [check_integrity, ]

    def delete_queryset(self, request, queryset):
        try:
            for branch in queryset:
                BranchService.remove_branch(branch.id)
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    def save_model(self, request, obj, form, change):
        destination_names = []
        for prefix in form.cleaned_data['destinations']:
            destination_names.append(prefix.name)

        body = form.cleaned_data
        body.pop('destinations')
        body['destination_names'] = destination_names
        body = json.dumps(body)
        if change:
            pass
            try:
                BranchService.update_branch(
                    obj.id,
                    body,
                )
            except api_exceptions.NotFound404 as e:
                self.message_user(request, e, level=messages.WARNING)
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)
        else:
            try:
                BranchService.add_branch(body)
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)

    def get_prefixes(self, obj):
        return ", ".join([p.prefix for p in obj.destinations.all()])

    get_prefixes.short_description = 'Prefixes'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['customer_code']
    list_display = (
        'id',
        'prime_code',
        'customer_code',
        'credit',
        'created_at',
        'updated_at',
    )
    list_filter = (
        ('created_at', DateRangeFilter),
    )
    list_per_page = 20
    readonly_fields = [
        'id',
        'prime_code',
        'customer_code',
        'subscriptions',
        'credit',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'prime_code',
                'customer_code',
                'credit',
                'subscriptions',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )

    actions = [check_integrity, ]

    def subscriptions(self, obj):
        link = ""
        for subscription in obj.subscriptions.all():
            url = reverse(
                "admin:finance_subscription_change",
                args=[subscription.id],
            )
            link += f'<a href="{url}">{subscription.subscription_code} </a>'

        return mark_safe(link)

    subscriptions.short_description = 'Subscriptions'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['subscription_code', 'number']
    list_display = (
        'id',
        'branch_link',
        'customer_link',
        'subscription_code',
        'subscription_type',
        'number',
        'auto_pay',
        'latest_paid_at',
        'created_at',
        'updated_at',
        'is_allocated',
        'deallocated_at',
        'deallocation_cause',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'branch_link',
                'customer_link',
                'subscription_code',

            ),
        }),
        ('Details', {
            'fields': (
                'subscription_type',
                'number',
                'is_allocated',
                'auto_pay',
                'interim_request',
                'deallocate_warned',
                'deallocation_cause',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'latest_paid_at',
                'created_at',
                'updated_at',
                'deallocated_at',
            ),
        }),
    )
    list_filter = (
        'auto_pay',
        'is_allocated',
        'subscription_type',
        'deallocation_cause',
        ('latest_paid_at', DateRangeFilter),
        ('created_at', DateRangeFilter),
        ('deallocated_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    readonly_fields = [
        'id',
        'customer_link',
        'auto_pay',
        'is_allocated',
        'latest_paid_at',
        'deallocated_at',
        'subscription_code',
        'subscription_type',
        'deallocation_cause',
        'branch_link',
        'number',
        'created_at',
        'updated_at',
    ]
    actions = [
        'add_interim',
        'renew_branch',
        'renew_subscription_type',
        'release_invoice_lock',
        'verify_repair_subscription',
        check_integrity,
    ]

    def add_interim(self, request, queryset):
        try:
            for subscription_object in queryset:
                InvoiceService.issue_interim_invoice(
                    subscription_code=subscription_object.subscription_code,
                    description=_('Created from Admin panel'),
                )
                message = _('New interim invoices issued')
                self.message_user(
                    request,
                    f"{message}: {subscription_object.subscription_code}",
                )
        except api_exceptions.Conflict409 as e:
            self.message_user(request, e, level=messages.WARNING)
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    add_interim.short_description = _('Add new interim invoice')

    def release_invoice_lock(self, request, queryset):
        for subscription_object in queryset:
            subscription_object.interim_processed()
        self.message_user(request, _("Subscriptions' locks are released"))

    release_invoice_lock.short_description = _("Release invoice lock")

    def renew_subscription_type(self, request, queryset):
        try:
            for subscription_object in queryset:
                SubscriptionService.renew_subscription_type(
                    subscription_id=subscription_object.id,
                )
            self.message_user(request, _("Subscription's type is renewed"))
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    renew_subscription_type.short_description = _("Renew subscription's type")

    def renew_branch(self, request, queryset):
        try:
            for subscription_object in queryset:
                SubscriptionService.renew_branch(
                    subscription_id=subscription_object.id,
                )
            self.message_user(request, _('Branches renewed'))
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    renew_branch.short_description = _("Renew subscription's branch")

    def customer_link(self, obj):
        url = reverse(
            "admin:finance_customer_change",
            args=[obj.customer.id],
        )
        link = f'<a href="{url}">{obj.customer.prime_code}</a>'

        return mark_safe(link)

    customer_link.short_description = 'Customer'

    def branch_link(self, obj):
        if obj.branch is None:
            return _('Not defined')

        url = reverse(
            "admin:finance_branch_change",
            args=[obj.branch.id],
        )
        link = f'<a href="{url}">{obj.branch.branch_code}</a>'

        return mark_safe(link)

    branch_link.short_description = 'Branch'

    def verify_repair_subscription(self, request, queryset):
        for subscription in queryset:
            if InvoiceService.verify_and_repair(
                    branch_code=subscription.branch.branch_code,
                    subscription_code=subscription.subscription_code
            ):
                messages.add_message(
                    request,
                    messages.INFO,
                    f"{subscription.subscription_code} balance repaired successfully",
                )
            else:
                messages.add_message(
                    request,
                    messages.INFO,
                    f"{subscription.subscription_code} balance is already correct",
                )

    verify_repair_subscription.short_description = _("Verify and repair subscription's balance")

    def delete_queryset(self, request, queryset):
        try:
            for subscription in queryset:
                SubscriptionService.remove_subscription(
                    subscription_code=subscription.subscription_code,
                )

        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RuntimeConfig)
class RuntimeConfigAdmin(admin.ModelAdmin):
    search_fields = ['item_key', 'item_value']
    list_display = ('item_key', 'item_value', 'created_at', 'updated_at')
    list_per_page = 20
    fieldsets = (
        ('Base Information', {
            'fields': (
                'item_key',
                'item_value',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    actions = [check_integrity, ]

    def delete_queryset(self, request, queryset):
        self.message_user(
            request,
            "Can not delete any RuntimeConfig",
            level=messages.WARNING,
        )
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['prefix', 'name']
    list_display = ('prefix', 'name', 'country_code', 'code')
    list_filter = (
        'code',
        ('created_at', DateRangeFilter),
    )
    list_per_page = 20
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'name',
            ),
        }),
        ('Details', {
            'fields': (
                'country_code',
                'code',
                'prefix',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    actions = [check_integrity, ]

    def delete_queryset(self, request, queryset):
        try:
            for destination in queryset:
                DestinationService.remove_destination(destination.id)
        except api_exceptions.Conflict409 as e:
            self.message_user(request, e, level=messages.WARNING)
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    def save_model(self, request, obj, form, change):
        if change:
            try:
                destination_serializer = DestinationSerializer(obj)
                DestinationService.update_destination(
                    obj.id,
                    json.dumps(destination_serializer.data),
                )
            except api_exceptions.NotFound404 as e:
                self.message_user(request, e, level=messages.WARNING)
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)
        else:
            try:
                destination_serializer = DestinationSerializer(obj)
                DestinationService.add_destination(json.dumps(
                    destination_serializer.data),
                )
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    search_fields = ['country_code']
    list_display = ('country_code', 'tax_percent',)
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': (
                'id',
                ('country_code', 'tax_percent'),
            ),
        }),
    )
    readonly_fields = [
        'id',
    ]
    actions = [check_integrity, ]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['id', 'package_name', 'package_code']
    list_display = (
        'id',
        'package_code',
        'package_name',
        'package_due',
        'package_discount',
        'package_price',
        'package_value',
        'is_active',
        'is_featured',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'package_code',
                'package_name',
            ),
        }),
        ('Details', {
            'fields': (
                'is_active',
                'is_featured',
                'package_due',
                'package_discount',
                'package_pure_price',
                'package_price',
                'package_value',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'start_at',
                'end_at',
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        "is_active",
        "is_featured",
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    actions = [check_integrity, ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in Package._meta.fields]

        return fields

    def delete_queryset(self, request, queryset):
        try:
            for package in queryset:
                PackageService.remove_package(package.id)
        except api_exceptions.Conflict409 as e:
            self.message_user(request, e, level=messages.WARNING)
        except api_exceptions.APIException as e:
            self.message_user(request, e, level=messages.ERROR)

    def save_model(self, request, obj, form, change):
        if change:
            try:
                package_serializer = PackageSerializer(obj)
                PackageService.update_package(
                    obj.id,
                    json.dumps(package_serializer.data),
                )
            except api_exceptions.NotFound404 as e:
                self.message_user(request, e, level=messages.WARNING)
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)
        else:
            try:
                package_serializer = PackageSerializer(obj)
                PackageService.add_package(json.dumps(
                    package_serializer.data),
                )
            except api_exceptions.APIException as e:
                self.message_user(request, e, level=messages.ERROR)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PackageInvoice)
class PackageInvoiceAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = [
        'id',
        'tracking_code',
        'subscription__subscription_code',
        'subscription__number',
    ]
    list_display = (
        'id',
        'subscription_link',
        'tracking_code',
        'created_at',
        'updated_status_at',
        'pay_cool_down',
        'status_code',
        'total_cost',
        'total_value',
        'expired_at',
        'is_active',
        'is_expired',
        'auto_renew',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'tracking_code',
                'subscription_link',
                'description',
                'status_code',
                'total_value',
                'total_cost',
                'expired_value',
                'is_expired',
                'auto_renew',
                'is_active',
                'expired_at',
                'related_package',
                'related_credit_invoice',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'pay_cool_down',
                'updated_status_at',
                'paid_at',
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        'status_code',
        ('updated_status_at', DateRangeFilter),
        ('created_at', DateRangeFilter),
        ('expired_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    actions = [check_integrity, ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in PackageInvoice._meta.fields]
        fields.append('subscription_link')
        fields.append('related_package')
        fields.append('related_credit_invoice')

        return fields

    def related_package(self, obj):
        link = "-"
        if obj.package:
            url = reverse(
                "admin:finance_package_change",
                args=[obj.package.id],
            )
            link = f'<a href="{url}">{obj.package.package_name}</a>'

        return mark_safe(link)

    related_package.short_description = 'Related package'

    def related_credit_invoice(self, obj):
        if obj.credit_invoice:
            url = reverse(
                "admin:finance_creditinvoice_change",
                args=[obj.credit_invoice.id],
            )
            link = f'<a href="{url}">{obj.credit_invoice.id}</a>'

            return mark_safe(link)
        return "-"

    related_credit_invoice.short_description = 'Related credit invoice'

    def subscription_link(self, obj):
        url = reverse(
            "admin:finance_subscription_change",
            args=[obj.subscription.id],
        )
        link = f'<a href="{url}">{obj.subscription.subscription_code}</a>'

        return mark_safe(link)

    subscription_link.short_description = 'Subscription'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BaseBalanceInvoice)
class BaseBalanceInvoiceAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = [
        'id',
        'tracking_code',
        'subscription__subscription_code',
        'subscription__number',
    ]
    list_display = (
        'id',
        'subscription_link',
        'tracking_code',
        'created_at',
        'pay_cool_down',
        'updated_status_at',
        'operation_type',
        'status_code',
        'total_cost',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'tracking_code',
                'subscription_link',
                'description',
                'operation_type',
                'status_code',
                'total_cost',
                'related_credit_invoice',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'pay_cool_down',
                'updated_status_at',
                'paid_at',
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        'status_code',
        'operation_type',
        ('updated_status_at', DateRangeFilter),
        ('created_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    actions = [check_integrity, ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in BaseBalanceInvoice._meta.fields]
        fields.append('subscription_link')
        fields.append('related_credit_invoice')

        return fields

    def related_credit_invoice(self, obj):
        if obj.credit_invoice:
            url = reverse(
                "admin:finance_creditinvoice_change",
                args=[obj.credit_invoice.id],
            )
            link = f'<a href="{url}">{obj.credit_invoice.id}</a>'

            return mark_safe(link)
        return "-"

    related_credit_invoice.short_description = 'Related credit invoice'

    def subscription_link(self, obj):
        url = reverse(
            "admin:finance_subscription_change",
            args=[obj.subscription.id],
        )
        link = f'<a href="{url}">{obj.subscription.subscription_code}</a>'

        return mark_safe(link)

    subscription_link.short_description = 'Subscription'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CreditInvoice)
class CreditInvoiceAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = [
        'id',
        'tracking_code',
        'customer__customer_code',
        'customer__subscriptions__number',
        'customer__subscriptions__subscription_code',
    ]
    list_display = (
        'id',
        'customer_link',
        'tracking_code',
        'created_at',
        'pay_cool_down',
        'updated_status_at',
        'operation_type',
        'used_for_link',
        'status_code',
        'total_cost',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'tracking_code',
                'customer_link',
                'operation_type',
                'status_code',
                'total_cost',
            ),
        }),
        ('Details', {
            'fields': (
                'description',
                'used_for_link',
                'used_for_id',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'pay_cool_down',
                'updated_status_at',
                'paid_at',
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        'status_code',
        ('updated_status_at', DateRangeFilter),
        ('created_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    actions = [check_integrity, ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in CreditInvoice._meta.fields]
        fields.append('customer_link')
        fields.append('used_for_link')

        return fields

    def customer_link(self, obj):
        url = reverse(
            "admin:finance_customer_change",
            args=[obj.customer.id],
        )
        link = f'<a href="{url}">{obj.customer.prime_code}</a>'

        return mark_safe(link)

    customer_link.short_description = 'Customer'

    def used_for_link(self, obj):
        if obj.used_for:
            if obj.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[0][0]:
                url = reverse(
                    "admin:finance_invoice_change",
                    args=[obj.used_for_id],
                )
            elif obj.used_for == \
                    FinanceConfigurations.CreditInvoice.USED_FOR[1][0]:
                url = reverse(
                    "admin:finance_basebalanceinvoice_change",
                    args=[obj.used_for_id],
                )
            else:
                url = reverse(
                    "admin:finance_packageinvoice_change",
                    args=[obj.used_for_id],
                )
            link = f'<a href="{url}">{obj.used_for_id}</a>'

            return mark_safe(link)

        return "-"

    used_for_link.short_description = 'Used for'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['id', 'credit_invoice__id']
    list_display = (
        'id',
        'related_credit_invoice',
        'created_at',
        'updated_status_at',
        'status_code',
        'amount',
    )
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'related_credit_invoice',
                'status_code',
            ),
        }),
        ('Details', {
            'classes': ('collapse',),
            'fields': (
                'amount',
                'gateway',
                'extra_data',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'updated_status_at',
                'created_at',
                'updated_at',
            ),
        }),
    )
    list_filter = (
        'status_code',
        ('updated_status_at', DateRangeFilter),
        ('created_at', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    actions = [check_integrity, ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in Payment._meta.fields]
        fields.append('related_credit_invoice')

        return fields

    def related_credit_invoice(self, obj):
        url = reverse(
            "admin:finance_creditinvoice_change",
            args=[obj.credit_invoice.id],
        )
        link = f'<a href="{url}">{obj.credit_invoice.id}</a>'

        return mark_safe(link)

    related_credit_invoice.short_description = 'Related credit invoice'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = [
        'id',
        'tracking_code',
        'subscription__subscription_code',
        'subscription__number',
    ]
    list_display = (
        'id',
        'subscription_link',
        'tracking_code',
        'created_at',
        'updated_status_at',
        'pay_cool_down',
        'from_date',
        'to_date',
        'due_date_notified',
        'is_overdue',
        'invoice_type_code',
        'status_code',
        'total_cost',
    )
    list_filter = (
        'status_code',
        'invoice_type_code',
        'due_date_notified',
        ('created_at', DateRangeFilter),
        ('updated_status_at', DateRangeFilter),
        ('due_date', DateRangeFilter),
    )
    ordering = ('-created_at',)
    list_per_page = 20
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'tracking_code',
                'subscription_link',
                'period_count',
                'invoice_type_code',
                'description',
                'status_code',
                'due_date_notified',
                'related_credit_invoice',
            ),
        }),
        ('Usage and Cost', {
            'classes': ('collapse',),
            'fields': (
                (
                    'landlines_local_usage',
                    'landlines_local_cost',
                ),
                (
                    'landlines_long_distance_usage',
                    'landlines_long_distance_cost',
                ),
                (
                    'landlines_corporate_usage',
                    'landlines_corporate_cost',
                ),
                (
                    'mobile_usage',
                    'mobile_cost',
                ),
                (
                    'international_usage',
                    'international_cost',
                ),
                (
                    'landlines_local_usage_prepaid',
                    'landlines_local_cost_prepaid',
                ),
                (
                    'landlines_long_distance_usage_prepaid',
                    'landlines_long_distance_cost_prepaid',
                ),
                (
                    'landlines_corporate_usage_prepaid',
                    'landlines_corporate_cost_prepaid',
                ),
                (
                    'mobile_usage_prepaid',
                    'mobile_cost_prepaid',
                ),
                (
                    'international_usage_prepaid',
                    'international_cost_prepaid',
                ),
                (
                    'total_usage_postpaid',
                    'total_usage_cost_postpaid',
                ),
                (
                    'total_usage_prepaid',
                    'total_usage_cost_prepaid',
                ),
                (
                    'total_usage',
                    'total_usage_cost',
                ),
                (
                    'tax_percent',
                    'tax_cost',
                ),
                (
                    'debt',
                    'subscription_fee',
                ),
                (
                    'discount',
                    'discount_description',
                ),
                'total_cost',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'from_date',
                'to_date',
                'due_date',
                'updated_status_at',
                'pay_cool_down',
                'paid_at',
                'created_at',
                'updated_at',
            ),
        }),
    )

    def safe_delete_invoice(self, request, queryset):
        """
        A common method for all models to check data integrity
        :param self:
        :param request:
        :param queryset:
        :return:
        """
        if len(queryset) != 1:
            messages.add_message(
                request,
                messages.ERROR,
                _("Can not safe delete more than one invoice at a time"),
            )
            return

        try:
            InvoiceService.delete_invoice(queryset[0].id)
            messages.add_message(
                request,
                messages.INFO,
                _("The invoice is safely deleted"),
            )
        except api_exceptions.APIException as e:
            messages.add_message(request, messages.ERROR, e)

    safe_delete_invoice.short_description = _('Safe delete invoice')
    actions = [check_integrity, safe_delete_invoice, ]

    def is_overdue(self, obj):
        return obj.is_overdue

    is_overdue.boolean = True

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in Invoice._meta.fields]
        fields.append('total_usage')
        fields.append('total_usage_cost')
        fields.append('subscription_link')
        fields.append('related_credit_invoice')

        return fields

    def related_credit_invoice(self, obj):
        if obj.credit_invoice:
            url = reverse(
                "admin:finance_creditinvoice_change",
                args=[obj.credit_invoice.id],
            )
            link = f'<a href="{url}">{obj.credit_invoice.id}</a>'

            return mark_safe(link)
        return "-"

    related_credit_invoice.short_description = 'Related credit invoice'

    def subscription_link(self, obj):
        url = reverse(
            "admin:finance_subscription_change",
            args=[obj.subscription.id],
        )
        link = f'<a href="{url}">{obj.subscription.subscription_code}</a>'

        return mark_safe(link)

    subscription_link.short_description = 'Subscription'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CommandRun)
class CommandRunAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['id', 'command_title', ]
    list_display = (
        'id',
        'command_title',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'command_title',
        ('created_at', DateRangeFilter),
    )

    ordering = ('-created_at',)
    list_per_page = 20
    fieldsets = (
        ('Info', {
            'fields': ('id', 'command_title')
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    actions = [check_integrity, ]

    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in CommandRun._meta.fields]

        return fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['id', 'file_id', 'payment_link', ]
    list_display = (
        'id',
        'payment_link',
        'file_id',
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at',)
    list_per_page = 20
    readonly_fields = [
        'id',
        'file_id',
        'payment_link',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'file_id',
                'payment_link',
            ),
        }),
        ('Dates', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )
    actions = [check_integrity, ]

    def payment_link(self, obj):
        link = "-"
        if obj.payment:
            url = reverse(
                "admin:finance_payment_change",
                args=[obj.payment.id],
            )
            link = f'<a href="{url}">{obj.payment.id}</a>'
        return mark_safe(link)

    payment_link.short_description = 'Payment'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
