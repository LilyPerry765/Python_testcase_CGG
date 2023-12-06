from django.utils.translation import gettext as _


class ErrorMessages:
    BASE_BALANCE_INVOICE_409 = _(
        "Can not be greater than the current base balance"
    )
    BASE_BALANCE_INVOICE_409_CURRENT = _(
        "Can not be greater than the current balance"
    )
    EXPORT_NO_DATA = _("No data returned to export")
    PROFIT_409_SAME = _("Current status code is th same with selected one")
    PROFIT_409 = _("Can not update profit from this status code")
    PROFIT_400_STATUS_CDOE = _("Invalid status code for profit")
    PAYMENT_409_CREDIT = _(
        "This item is payed with the existing credit, so it does not have "
        "any payments"
    )
    PAYMENT_409_RELATED = _(
        "This item is not payed, so it does not have any payments"
    )
    PACKAGE_INVOICE_409 = _(
        "A package is already active, can not create a new one",
    )
    PACKAGE_404 = _("Package does not exists")
    PACKAGE_INVOICE_404 = _("Package invoice does not exists")
    TRACKING_CODE_400 = _('Must be string')
    CREDIT_INVOICE_409 = _("Decreasing credit must have a reason")
    SUBSCRIPTION_409_CREDIT = _("Subscription does not have enough credit")
    INVOICE_404_PAY = _("Trying to update an invoice that does not exists")
    BASE_BALANCE_INVOICE_404_PAY = _(
        "Trying to update a base balance invoice that does not exists",
    )
    PACKAGE_INVOICE_404_PAY = _(
        "Trying to update a package invoice that does not exists",
    )
    OPERATOR_404 = _("Operator does not exists")
    CUSTOMER_404 = _("Customer does not exists")
    CUSTOMER_409 = _("Customer does not have any subscription")
    CUSTOMER_CODE_400 = _("Invalid customer code")
    SUBSCRIPTION_404 = _("Subscription does not exists")
    SUBSCRIPTION_409 = _("Subscription does not belongs to this customer")
    SUBSCRIPTION_409_UNLIMITED = _("This subscription is unlimited")
    SUBSCRIPTION_409_PREPAID = _("This subscription is prepaid")
    SUBSCRIPTION_ALLOCATED_404 = _(
        'Subscription does not exists or is not allocated',
    )
    SUBSCRIPTION_NUMBER_400 = _("Invalid subscription's number")
    SUBSCRIPTION_TYPE_400 = _("Invalid subscription's type")
    SUBSCRIPTION_CODE_400 = _("Invalid subscription's number")
    BASE_BALANCE_INVOICE_404 = _("Base balance invoice does not exists")
    GENERIC_404 = _("with this id does not exist")
    PAYMENT_409_COOL_DOWN = _(
        "A pay request for this invoice is still waiting for it's response, "
        "try again in later"
    )
    PAYMENT_409_COOL_DOWN_PREVIOUS = _(
        "A pay request for the previous invoice is still waiting for it's "
        "response, try again in later"
    )
    CREDIT_INVOICE_404 = _("Credit invoice does not exists")
    INVOICE_404 = _("Invoice does not exists")
    PAYMENT_404 = _("Payment does not exists")
    BRANCH_404 = _("Branch does not exists")
    PROFIT_404 = _("Profit does not exists")
    BRANCH_CODE_400 = _("Invalid branch code")
    BRANCH_NAME_400 = _("Invalid branch name")
    ORDER_BY_400 = _("Invalid choices in order by query")
    DESTINATION_404 = _("Destination does not exists")
    DESTINATION_PREFIX_400 = _("Invalid destination prefix")
    DESTINATION_NAME_400 = _("Invalid destination name")
    DESTINATION_COUNTRY_CODE_400 = _("Invalid destination country code")
    DESTINATION_CODE_400 = _("Invalid destination code")
    DATE_TIME_400 = _("Datetime parsing error")
    TOTAL_COST_400 = _("Total cost must be a number")
    VALID_CHOICES_400 = _("Valid choices are")
    STRING_400 = _("Must be string")
    BOOLEAN_400 = _('Must be boolean')
    JSON_BODY_400 = _('Body can not be empty')
    REQUIRED_FIELD_400 = _('This field is required')
    OPERATOR_CODE_400 = _("Invalid operator code")
    PACKAGE_NAME_400 = _("Invalid package name")
    PACKAGE_VALUE_400 = _("Invalid package value")
    PACKAGE_PRICE_400 = _("Invalid package price")
    PACKAGE_DUE_400 = _("Invalid package due")
    PACKAGE_IS_ACTIVE_400 = _("Invalid package is active")
    PACKAGE_IS_FEATURED_400 = _("Invalid package is featured")
    PACKAGE_START_DATE_400 = _("Invalid start date")
    PACKAGE_END_DATE_400 = _("Invalid end date")
    PACKAGE_START_DATE_GREATER_400 = _(
        "Start date can not be greater than end date"
    )
