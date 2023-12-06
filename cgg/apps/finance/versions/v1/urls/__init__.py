from django.urls import re_path

from cgg.apps.finance.versions.v1.api import api

urls = [
    ############################################
    #            Branch related URLs          #
    ############################################
    # Get all branches
    re_path(
        r'^(?:v1/)?branches(?:/)?$',
        api.BranchesAPIView.as_view(),
        name='branches'
    ),
    # Get an branch
    re_path(
        r'^(?:v1/)?branches/(?P<branch_id>[^/]+)(?:/)?$',
        api.BranchAPIView.as_view(),
        name='branch'
    ),
    ############################################
    #            Customer related URLs          #
    ############################################
    # Get all customers
    re_path(
        r'^(?:v1/)?customers(?:/)?$',
        api.CustomersAPIView.as_view(),
        name='customers'
    ),
    # Get an customer
    re_path(
        r'^(?:v1/)?customers/(?P<customer>[^/]+)(?:/)?$',
        api.CustomerAPIView.as_view(),
        name='customer'
    ),
    # Increase customer's credit (No pay mode)
    re_path(
        r'^(?:v1/)?customers/(?P<customer>[^/]+)/credit(?:/)?$',
        api.SubscriptionIncreaseCreditAPIView.as_view(),
        name='customer_credit'
    ),
    ############################################
    #       Subscription related URLs          #
    ############################################
    # Subscriptions
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?anti-subscriptions(?:/)?$',
        api.SubscriptionsAntiAPIView.as_view(),
        name='subscriptions_anti'
    ),
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions(?:/)?$',
        api.SubscriptionsAPIView.as_view(),
        name='subscriptions'
    ),
    # Subscription
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)(?:/)?$',
        api.SubscriptionAPIView.as_view(),
        name='subscription'
    ),
    # Empower subscription
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/availability(?:/)?$',
        api.SubscriptionAvailabilityAPIView.as_view(),
        name='subscription_availability'
    ),
    # Debit balance from subscription
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/debit-balance(?:/)?$',
        api.SubscriptionDebitBalanceAPIView.as_view(),
        name='subscription_debit_balance'
    ),
    # Add balance to subscription
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/add-balance(?:/)?$',
        api.SubscriptionAddBalanceAPIView.as_view(),
        name='subscription_add_balance'
    ),
    # Deallocate subscription
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/deallocate(?:/)?$',
        api.SubscriptionDeallocateAPIView.as_view(),
        name='subscription_deallocate'
    ),
    # Increase subscription's credit (No pay mode)
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/credit(?:/)?$',
        api.SubscriptionIncreaseCreditAPIView.as_view(),
        name='subscription_increase_credit'
    ),
    # Increase subscription's base balance (No pay mode)
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/base-balance(?:/)?$',
        api.SubscriptionChangeBaseBalanceAPIView.as_view(),
        name='subscription_change_base_balance'
    ),
    # Convert prepaid to postpaid
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?subscriptions/('
        r'?P<subscription>[^/]+)/convert(?:/)?$',
        api.SubscriptionConvertAPIView.as_view(),
        name='subscription_convert'
    ),
    ############################################
    #            Invoice related URLs          #
    ############################################
    # Invoices
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?invoices(?:/)?$',
        api.InvoicesAPIView.as_view(),
        name='invoices'
    ),
    # Invoice
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?invoices/(?P<invoice>[^/]+)(?:/)?$',
        api.InvoiceAPIView.as_view(),
        name='invoice'
    ),
    # Export invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/(customers/(?P<customer>['
        r'^/]+)/)?(subscriptions/(?P<subscription>[^/]+)/)?invoices(?:/)?$',
        api.ExportInvoicesAPIView.as_view(),
        name='export_invoices'
    ),
    ############################################
    #        Package invoice related URLs      #
    ############################################
    # Package invoices
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?package-invoices(?:/)?$',
        api.PackageInvoicesAPIView.as_view(),
        name='package_invoices'
    ),
    # Package invoice
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?package-invoices/(?P<package_invoice>['
        r'^/]+)(?:/)?$',
        api.PackageInvoiceAPIView.as_view(),
        name='package_invoice'
    ),
    # Export package invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/(customers/(?P<customer>['
        r'^/]+)/)?(subscriptions/(?P<subscription>[^/]+)/)?package-invoices(?:/)?$',
        api.ExportPackageInvoicesAPIView.as_view(),
        name='export_package_invoices'
    ),
    ############################################
    #   Base balance invoice related URLs      #
    ############################################
    # Base balance invoices
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?base-balance-invoices(?:/)?$',
        api.BaseBalanceInvoicesAPIView.as_view(),
        name='base_balance_invoices'
    ),
    # Base balance invoice
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?base-balance-invoices/(?P<base_balance>['
        r'^/]+)(?:/)?$',
        api.BaseBalanceInvoiceAPIView.as_view(),
        name='base_balance_invoice'
    ),
    # Export base balance invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/(customers/(?P<customer>['
        r'^/]+)/)?(subscriptions/(?P<subscription>['
        r'^/]+)/)?base-balance-invoices(?:/)?$',
        api.ExportBaseBalanceInvoicesAPIView.as_view(),
        name='export_base_balance_invoices'
    ),
    ############################################
    #         Credit invoice related URLs      #
    ############################################
    # Credit invoices
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?credit-invoices(?:/)?$',
        api.CreditInvoicesAPIView.as_view(),
        name='credit_invoices'
    ),
    # Credit invoices
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?credit-invoices/(?P<credit>['
        r'^/]+)(?:/)?$',
        api.CreditInvoiceAPIView.as_view(),
        name='credit_invoice'
    ),
    # Export credit invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/(customers/(?P<customer>['
        r'^/]+)/)?(subscriptions/(?P<subscription>['
        r'^/]+)/)?credit-invoices(?:/)?$',
        api.ExportCreditInvoicesAPIView.as_view(),
        name='export_credit_invoices'
    ),
    ############################################
    #            Payment related URLs          #
    ############################################
    # Payments
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?((credit-invoices/(?P<credit_invoice>['
        r'^/]+)/)|(base-balance-invoices/(?P<base_balance_invoice>[^/]+)/)|('
        r'package-invoices/(?P<package_invoice>[^/]+)/)|(invoices/('
        r'?P<invoice>[^/]+)/))?payments(?:/)?$',
        api.PaymentsAPIView.as_view(),
        name='payments'
    ),
    # A Payment
    re_path(
        r'^(?:v1/)?(customers/(?P<customer>[^/]+)/)?(subscriptions/('
        r'?P<subscription>[^/]+)/)?((credit-invoices/(?P<credit_invoice>['
        r'^/]+)/)|(base-balance-invoices/(?P<base_balance_invoice>[^/]+)/)|('
        r'package-invoices/(?P<package_invoice>[^/]+)/)|(invoices/('
        r'?P<invoice>[^/]+)/))?payments/(?P<payment>[^/]+)(?:/)?$',
        api.PaymentAPIView.as_view(),
        name='payment'
    ),
    # All Payments
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/(customers/(?P<customer>['
        r'^/]+)/)?(subscriptions/(?P<subscription>[^/]+)/)?(('
        r'credit-invoices/(?P<credit_invoice>[^/]+)/)|('
        r'base-balance-invoices/(?P<base_balance_invoice>[^/]+)/)|('
        r'package-invoices/(?P<package_invoice>[^/]+)/)|(invoices/('
        r'?P<invoice>[^/]+)/))?payments(?:/)?$',
        api.PaymentsExportAPIView.as_view(),
        name='export_payments'
    ),
    # Approval of a Payment
    re_path(
        r'^(?:v1/)?payments/(?P<payment>[^/]+)/approval(?:/)?$',
        api.PaymentApprovalAPIView.as_view(),
        name='payment_approval'
    ),
    ############################################
    #          Profit related URLs            #
    ############################################
    # Get list of operator and add new one
    re_path(
        r'^(?:v1/)?operators(?:/)?$',
        api.OperatorsAPIView.as_view(),
        name='operators'
    ),
    # Get or update a operator
    re_path(
        r'^(?:v1/)?operators/(?P<operator>[^/]+)(?:/)?$',
        api.OperatorAPIView.as_view(),
        name='operator'
    ),
    # Get list of profits and add new one
    re_path(
        r'^(?:v1/)?profits(?:/)?$',
        api.ProfitsAPIView.as_view(),
        name='profits'
    ),
    # Export list of profits
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/profits(?:/)?$',
        api.ExportProfitsAPIView.as_view(),
        name='export_profits'
    ),
    # Get or update a profit
    re_path(
        r'^(?:v1/)?profits/(?P<profit>[^/]+)(?:/)?$',
        api.ProfitAPIView.as_view(),
        name='profit'
    ),
    ############################################
    #          Package related URLs        #
    ############################################
    re_path(
        r'^(?:v1/)?packages(?:/)?$',
        api.PackagesAPIView.as_view(),
        name='packages'
    ),
    re_path(
        r'^(?:v1/)?packages/(?P<package>[^/]+)(?:/)?$',
        api.PackageAPIView.as_view(),
        name='package'
    ),
    ############################################
    #          Destination related URLs        #
    ############################################
    # Get list and add Prefixes
    re_path(
        r'^(?:v1/)?destinations(?:/)?$',
        api.DestinationsAPIView.as_view(),
        name='ratings_destinations'
    ),
    # Get list and add Prefixes group by name
    re_path(
        r'^(?:v1/)?destinations/names(?:/)?$',
        api.DestinationsNamesAPIView.as_view(),
        name='ratings_destinations_names'
    ),
    # Get a Prefix
    re_path(
        r'^(?:v1/)?destinations/(?P<destination>[^/]+)(?:/)?$',
        api.DestinationAPIView.as_view(),
        name='ratings_destination'
    ),
    ############################################
    #          CGRateS related URLs            #
    # /cgrates/<str:function_name>/<str:type>  #
    ############################################
    # get new any kind of notifications from cgrates
    re_path(
        r'^(?:v1/)?cgrates/notification/(?P<notify_type>[^/]+)(?:/)?$',
        api.CGRateSNotificationAPIView.as_view(),
        name='cgrates_notification'
    ),
    re_path(
        r'^(?:v1/)?cgrates/expiry/(?P<subscription_code>[^/]+)(?:/)?$',
        api.CGRateSExpiryAPIView.as_view(),
        name='cgrates_expiry'
    ),
    ############################################
    #          Migration related URLs          #
    #      /migration/<str:function_name>/     #
    ############################################
    # Migrate all bills and payments
    re_path(
        r'^(?:v1/)?migration/invoices(?:/)?$',
        api.MigrateInvoicesAPIView.as_view(),
        name='migration_invoices'
    ),
    # Migrate all bills and payments
    re_path(
        r'^(?:v1/)?migration/base-balance-invoices(?:/)?$',
        api.MigrateBaseBalanceInvoicesAPIView.as_view(),
        name='migration_base_balance_invoices'
    ),
    ############################################
    #       RuntimeConfig related URLs         #
    ############################################
    # Get or update RuntimeConfigs (Partial)
    re_path(
        r'^(?:v1/)?runtime-configs(?:/)?$',
        api.RuntimeConfigsAPIView.as_view(),
        name='runtime_configs'
    ),
]
