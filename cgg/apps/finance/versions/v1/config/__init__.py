# --------------------------------------------------------------------------
# Basic labels and config methods for finance application
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - __init__.py
# Created at 2020-5-16,  12:12:22
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.conf import settings
from django.utils.translation import get_language, gettext as _


class FinanceConfigurations:
    class Export:
        class Format:
            CSV = 'csv'
            XML = 'xml'
            PDF = 'pdf'
            JSON = 'json'

            @classmethod
            def is_json(cls, format_name):
                if format_name == cls.JSON or (format_name not in [
                    cls.XML,
                    cls.PDF,
                    cls.CSV,
                ]
                ):
                    return True

                return False

            @classmethod
            def is_pdf(cls, format_name):
                if format_name == cls.PDF:
                    return True

                return False

            @classmethod
            def is_csv(cls, format_name):
                if format_name == cls.CSV:
                    return True

                return False

            @classmethod
            def is_xml(cls, format_name):
                if format_name == cls.XML:
                    return True

                return False

    @staticmethod
    def default_headers():
        return {
            'Accept-Language': get_language(),
        }

    class QueryParams:
        FRIENDLY = 'friendly'
        OPERATION_TYPE = 'operation_type'
        GATEWAY = 'gateway'
        GENERIC_OR = 't'
        SUBSCRIPTION_CODE = 'subscription_code'
        PRIME_CODE = 'prime_code'
        ID = 'id'
        NUMBER = 'number'
        STATUS_CODE = 'status_code'
        TOTAL_COST_FROM = 'total_cost_from'
        TOTAL_COST_TO = 'total_cost_to'
        TRACKING_CODE = 'tracking_code'
        CREATED_AT_FROM = 'created_at_from'
        UPDATED_AT_FROM = 'updated_at_from'
        CREATED_AT_TO = 'created_at_to'
        UPDATED_AT_TO = 'updated_at_to'
        PAID_AT_FROM = 'paid_at_from'
        PAID_AT_TO = 'paid_at_to'
        FROM_DATE_FROM = 'from_date_from'
        TO_DATE_FROM = 'to_date_from'
        FROM_DATE_TO = 'from_date_to'
        TO_DATE_TO = 'to_date_to'
        ORDER_BY = 'order_by'
        INVOICE_TYPE_CODE = 'invoice_type_code'

    class APIRequestLabels:
        INCREASE_CUSTOMER_CREDIT = "Increase credit (no pay mode)"
        CHANGE_SUBSCRIPTION_BASE_BALANCE = "Change base balance (no pay mode)"
        EXPORT_PAYMENTS = "Export payments"
        EXPORT_CREDIT_INVOICES = "Export credit invoices"
        EXPORT_PACKAGE_INVOICES = "Export package invoices"
        EXPORT_INVOICES = "Export invoices"
        EXPORT_BASE_BALANCE_INVOICES = "Export base balance invoices"
        EXPORT_PROFITS = "Export profits"
        UPDATE_RUNTIME_CONFIGS = "Update runtime configs"
        GET_RUNTIME_CONFIGS = "Get runtime configs"
        UPDATE_SUBSCRIPTION_CONVERT = "Convert subscription"
        UPDATE_PACKAGE_INVOICE = "Update package invoice"
        EXPIRY_NOTIFICATION = "Expiry notification"
        REMOVE_PACKAGE = "Remove a package"
        UPDATE_PACKAGE = "Update a package"
        GET_PACKAGE = "Get package"
        ADD_PACKAGE = "Add package"
        GET_PACKAGES = "Get packages"
        GET_PACKAGE_INVOICE = "Get package invoice"
        CREATE_PACKAGE_INVOICE = "Create package invoice"
        GET_CREDIT_INVOICES = "Get credit invoice"
        CREATE_CREDIT_INVOICE = "Create credit invoice"
        GET_CREDIT_INVOICE = "Get credit invoice"
        MIGRATE_BASE_BALANCE_INVOICES = "Migrate base balance invoices"
        MIGRATE_INVOICES = "Migrate invoices"
        DELETE_BRANCH = "Delete branch"
        GET_DESTINATIONS_NAMES = "Get destination names"
        GET_PROFITS = "Get profits"
        GET_PROFIT = "Get profit"
        UPDATE_PROFIT = "Update profit"
        ADD_PROFIT = "Add profit"
        GET_OPERATOR = "Get operator"
        GET_OPERATORS = "Get operators"
        ADD_OPERATOR = "Add operator"
        UPDATE_OPERATOR = "Update operator"
        DELETE_OPERATOR = "Delete operator"
        UPDATE_SUBSCRIPTION = "Update subscription"
        REMOVE_SUBSCRIPTION = "Remove subscription"
        UPDATE_BRANCH = "Update branch"
        GET_BRANCH = "Branch"
        ADD_BRANCH = "Add branch"
        GET_BRANCHES = "Branches"
        SUBSCRIPTION_DEALLOCATE = "Deallocate subscription"
        UPDATE_DESTINATION = 'Update destination'
        REMOVE_DESTINATION = 'Remove destination'
        GET_DESTINATIONS = 'Get destinations'
        GET_DESTINATION = 'Get destination'
        ADD_DESTINATION = 'Add new destination'
        POST_TO_TRUNK = 'Post to trunk'
        SUBSCRIPTION_DEBIT_BALANCE = "Debit balance subscription"
        SUBSCRIPTION_ADD_BALANCE = "Add balance subscription"
        ADD_SUBSCRIPTION = "Add Subscription"
        ADD_CUSTOMER = "Add customer"
        CHANGE_SUBSCRIPTION_AVAILABILITY = "Change subscription availability"
        GET_SUBSCRIPTION_AVAILABILITY = "Get subscription availability"
        GET_CUSTOMERS = 'Customers'
        GET_CUSTOMER = 'Customer'
        GET_SUBSCRIPTION = 'Subscription'
        GET_SUBSCRIPTIONS = 'Subscriptions'
        GET_SUBSCRIPTIONS_ANTI = 'Subscriptions (anti pattern mode)'
        GET_INVOICES = 'Invoices'
        GET_INVOICE = 'Invoice'
        CREATE_INTERIM_INVOICE = 'Interim invoice'
        CREATE_PERIOD_INVOICE = 'Period invoice'
        GET_PAYMENTS = 'Payments'
        GET_PAYMENT = 'Get payment'
        UPDATE_PAYMENT = 'Update payment'
        ADD_PAYMENT = 'Add payment'
        APPROVE_PAYMENT = 'Approve payment'
        GET_BASE_BALANCE_INVOICE = 'Base balance invoice'
        GET_BASE_BALANCE_INVOICES = 'Base balance invoices'
        GET_PACKAGE_INVOICES = 'Package invoices'
        CREATE_BASE_BALANCE_INVOICE = 'New base balance invoice'
        USAGE_NOTIFICATION = 'Usage notification'
        GET_SUBSCRIPTION_FEE = 'Get subscription fee'

    class Package:
        DEFAULT_PACKAGE_CODE = (
            'default',
            _('Default'),
        )
        TYPES = (
            ('1', _('1 Day')),
            ('3', _('3 Days')),
            ('5', _('5 Days')),
            ('7', _('7 Days')),
            ('15', _('15 Days')),
            ('30', _('30 Days')),
            ('45', _('45 Days')),
            ('60', _('60 Days')),
            ('90', _('90 Days')),
            ('120', _('120 Days')),
            ('180', _('180 Days')),
            ('365', _('365 Days')),
        )

    class Notify:
        PostpaidEightyPercent = "postpaid-eighty"
        PrepaidEightyPercent = "prepaid-eighty"
        PostpaidMaxUsage = "postpaid-max"
        PrepaidMaxUsage = "prepaid-max"
        PrepaidExpire = "prepaid-expire"

    class Destination:
        # This value is used in filtering CDRs when no prefixes match
        NOT_FOUND_PREFIX = "PREFIX_NOT_FOUND"
        CODE_CHOICES = (
            ('mobile_national', _('Mobile national')),
            ('landline_national', _('Landline national')),
            ('mobile_international', _('Mobile International')),
            ('landline_international', _('Landline International')),
        )
        UNUSED_TYPES = (
            ('operator', _('Operator')),
            ('branch', _('Branch')),
        )
        CORPORATE_DEFAULT_NAME = ("corporate", "Corporate")
        EMERGENCY_NAME = ("emergency", "Emergency")

    class Profit:
        STATE_CHOICES = (
            ('pending', _('Pending')),
            ('received', _('Received')),
            ('revoked', _('Revoked')),
        )
        RATE_TIME_TYPE = (
            ('seconds', _('Seconds')),
            ('minutes', _('Minutes')),
        )

    class Subscription:
        TYPE = (
            ('postpaid', _('Postpaid')),
            ('prepaid', _('Prepaid')),
            ('unlimited', _('Unlimited')),
        )
        DEALLOCATION_CAUSE = (
            ('normal', _('Normal')),
            ('violation', _('Violation')),
        )

    class Invoice:
        class BypassType:
            NO_BYPASS = "no_bypass"
            EIGHTY_PERCENT = "eighty_bypass"
            MAX_USAGE = "max_usage_bypass"
            DEALLOCATE = "deallocate_bypass"

        DUE_DATE_NOTIFY = (
            ('no_warning', _('No warning')),
            ('first_warning', _('First warning')),
            ('second_warning', _('Second warning')),
            ('third_warning', _('Third warning')),
            ('fourth_warning', _('Fourth warning')),
        )
        STATE_CHOICES = (
            ('ready', _('Ready')),
            ('pending', _('Pending')),
            ('success', _('Success')),
            ('revoke', _('Revoke')),
        )
        TYPES = (
            ('periodic', _('Periodic')),
            ('interim', _('Interim')),
        )

    class CreditInvoice:
        OPERATION_TYPES = (
            ('increase', _('Increase')),
            ('decrease', _('Decrease')),
        )
        USED_FOR = (
            ('invoice', _('Invoice')),
            ('base_balance_invoice', _('Base balance invoice')),
            ('package_invoice', _('Package invoice')),
        )

    class Payment:
        STATE_CHOICES = (
            ('pending', _('Pending')),
            ('success', _('Success')),
            ('failed', _('Failed')),
        )
        OFFLINE = "offline"

    class RuntimeConfig:
        KEY_CHOICES = (
            (
                'issue_new_interim_hours',
                _('Issue new interim invoice in hours')),
            (
                'invoice_due_dates_period',
                _('Number of periods for due date in invoices'),
            ),
            (
                'corporate_state_prefixes',
                _('Corporate state prefixes'),
            ),
            (
                'corporate_national_prefixes',
                _('Corporate national prefixes'),
            ),
            (
                'discount_static_value',
                _('Discount static value on invoices'),
            ),
            (
                'discount_percent_value',
                _('Discount percent on invoices'),
            ),
            (
                'deallocation_due',
                _('Due date for deallocation of subscription'),
            ),
            (
                'emergency_numbers',
                _('Emergency numbers'),
            ),
            (
                'payment_cool_down',
                _('Payment cool down in minutes'),
            ),
            (
                'black_list_in_days',
                _('Black list deallocated numbers in days'),
            ),
        )
        # These are used in update runtime config, sync this with KEY_CHOICES
        DEFAULT_VALUES = {
            "issue_new_interim_hours": "3",
            "invoice_due_dates_period": "2",
            "corporate_state_prefixes": "9200,9107",
            "corporate_national_prefixes": "94260,94200",
            "discount_static_value": "0",
            "discount_percent_value": "0",
            "deallocation_due": "365",
            "emergency_numbers": "110,112,115,125",
            "payment_cool_down": "15",
            "black_list_in_days": "730",
        }

    class Branch:
        DEFAULT_BRANCH_CODE = (
            'default',
            _('Default'),
        )
        DEFAULT_COUNTRY_BRANCH = (
            'country',
            _('Country'),
        )
        DEFAULT_EMERGENCY_BRANCH = (
            'emergency',
            _('Emergency'),
        )

    class Commands:
        TYPES = (
            ('periodic_invoices', _('Periodic invoices')),
            ('due_date', _('Due date')),
            ('failed_jobs', _('Failed jobs')),
            ('renew_branches', _('Renew branches')),
            ('import_destinations', _('Import destinations')),
            ('import_tariffs', _('Import tariffs')),
            ('init_cgrates', _('Initialize CGRateS')),
            ('import_credits', _('Import credits from Excel')),
            ('import_branches', _('Import branches')),
            ('renew_subscription_type', _("Renew subscription's type")),
            ('expire_packages', _("Expire packages")),
            ('integrity_check', _("Integrity check")),
            ('update_runtime_configs', _("Update runtime configs")),
            ('check_deallocation', _("Check deallocation")),
            ('clean_api_requests', _("Clean api requests")),
            ('check_sessions', _("Check sessions")),
        )

    class Jobs:
        TYPES = (
            ('periodic_invoice', _('Periodic invoices')),
            ('notify_trunk', _('Notify trunk')),
            ('renew_branch', _('Renew branch')),
            ('renew_subscription_type', _('Renew subscription type')),
        )

    class TrunkBackend:
        URLs = settings.CGG['RELATIVE_URLS']['TRUNK_BACKEND']

        class Notify:
            DUE_DATE_WARNING_1 = "DUE_DATE_WARNING_1"
            DUE_DATE_WARNING_2 = "DUE_DATE_WARNING_2"
            DUE_DATE_WARNING_3 = "DUE_DATE_WARNING_3"
            DUE_DATE_WARNING_4 = "DUE_DATE_WARNING_4"
            PERIODIC_INVOICE = "PERIODIC_INVOICE"
            INTERIM_INVOICE = "INTERIM_INVOICE"
            INTERIM_INVOICE_AUTO_PAYED = "INTERIM_INVOICE_AUTO_PAYED"
            PREPAID_RENEWED = "PREPAID_RENEWED"
            PREPAID_EXPIRED = "PREPAID_EXPIRED"
            PREPAID_MAX_USAGE = "PREPAID_MAX_USAGE"
            PREPAID_EIGHTY_PERCENT = "PREPAID_EIGHTY_PERCENT"
            POSTPAID_MAX_USAGE = "POSTPAID_MAX_USAGE"
            DEALLOCATION_WARNING_1 = "DEALLOCATION_WARNING_1"
            DEALLOCATION_WARNING_2 = "DEALLOCATION_WARNING_2"

        @classmethod
        def default_headers(cls):
            return {
                'Accept-Language': get_language(),
                'Authorization': settings.CGG['AUTH_TOKENS'][
                    'TRUNK_OUT'],
            }

        @classmethod
        def get_base_url(cls):
            return settings.CGG['BASE_URLS'][
                'TRUNK_BACKEND'].rstrip('/')

        @classmethod
        def url_interim_invoice(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['INTERIM_INVOICE'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_prepaid_eighty_percent(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['PREPAID_EIGHTY_PERCENT'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_periodic_invoice(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['PERIODIC_INVOICE'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_postpaid_max_usage(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['POSTPAID_MAX_USAGE'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_interim_invoice_auto_payed(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['INTERIM_INVOICE_AUTO_PAYED'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_prepaid_max_usage(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['PREPAID_MAX_USAGE'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_prepaid_expired(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['PREPAID_EXPIRED'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_prepaid_renewed(cls):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['PREPAID_RENEWED'].strip('/')
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_due_date(cls, warning_type):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['DUE_DATE'].strip('/').format(
                warning_type=warning_type,
            )
            return f"{base_url}/{relative_url}/"

        @classmethod
        def url_deallocation(cls, warning_type):
            base_url = cls.get_base_url()
            relative_url = cls.URLs['DEALLOCATION'].strip('/').format(
                warning_type=warning_type,
            )
            return f"{base_url}/{relative_url}/"

    class Mis:
        API_RELATIVE_URLS = {
            "SUBSCRIPTION_FEE": "/api/Nexfon/calculateBill"
        }
