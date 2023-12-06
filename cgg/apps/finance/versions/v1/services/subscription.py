# --------------------------------------------------------------------------
# Handles the logic for Subscription related jobs. From creating, updating
# and removing to no pay mode jobs. Any change in here changes the data in
# CGRateS as well.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - subscription.py
# Created at 2020-8-29,  17:43:19
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import CharField, F, Value
from django.utils.translation import gettext as _

from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions,
)
from cgg.apps.basic.versions.v1.services.basic import BasicService
from cgg.apps.finance.models import (
    Customer,
    Destination,
    Package,
    PackageInvoice,
    Subscription,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.base_balance_invoice import (
    BaseBalanceInvoiceSerializer,
)
from cgg.apps.finance.versions.v1.serializers.customer import (
    CustomerSerializer,
)
from cgg.apps.finance.versions.v1.serializers.subscription import (
    ChangeBalanceSerializer,
    SubscriptionAntiSerializer,
    SubscriptionBaseBalanceSerializer,
    SubscriptionConvertSerializer,
    SubscriptionDeallocationSerializer,
    SubscriptionSerializer,
    SubscriptionUpdateSerializer,
)
from cgg.apps.finance.versions.v1.services.base_balance_invoice import (
    BaseBalanceInvoiceService,
)
from cgg.apps.finance.versions.v1.services.branch import BranchService
from cgg.apps.finance.versions.v1.services.common import CommonService
from cgg.apps.finance.versions.v1.services.customer import CustomerService
from cgg.apps.finance.versions.v1.services.package_invoice import (
    PackageInvoiceService,
)
from cgg.apps.finance.versions.v1.services.runtime_config import (
    RuntimeConfigService,
)
from cgg.core import api_exceptions
from cgg.core.error_messages import ErrorMessages
from cgg.core.paginator import Paginator
from cgg.core.tools import Tools

SUBSCRIPTION_TYPES = FinanceConfigurations.Subscription.TYPE


class SubscriptionService:

    @classmethod
    def get_subscription_from_cgrates(cls, subscription, force_reload=False):
        """
        Get subscription details from CGRateS Service
        :param force_reload:
        :param subscription:
        :return:
        """
        print('start get_subscription_from_cgrates')
        balance_details = BasicService.get_balance(
            subscription.subscription_code,
            force_reload,
        )

        if balance_details:
            subscription_serializer = SubscriptionSerializer(
                subscription,
                context=balance_details,
            )
        else:
            return []

        return subscription_serializer.data

    @classmethod
    def get_subscription(
            cls,
            customer_code,
            subscription_code,
            query_params,
    ):
        """
        Get details of a subscription
        :param query_params:
        :param customer_code:
        :param subscription_code:
        :return:
        """
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        force_reload = False
        if 'force_reload' in query_params:
            force_reload = True
        subscription_details = cls.get_subscription_from_cgrates(
            subscription_object,
            force_reload,
        )

        return subscription_details

    @classmethod
    def update_subscription(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Force update base balance and other details of a subscription
        (@TODO: Change theses functionality after a while)
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        base_balance = None
        used_balance = None
        credit = None
        auto_pay = None
        body = Tools.get_dict_from_json(body)
        update_subscription = SubscriptionUpdateSerializer(
            data=body,
        )
        # Remove these fearless updates after migrations (base, used, credit)
        if update_subscription.is_valid(raise_exception=True):
            if 'base_balance' in update_subscription.data:
                base_balance = int(
                    float(update_subscription.data['base_balance'])
                )
            if 'used_balance' in update_subscription.data:
                used_balance = int(
                    float(update_subscription.data['used_balance'])
                )
            if 'credit' in update_subscription.data:
                credit = int(
                    float(update_subscription.data['credit'])
                )
            if 'auto_pay' in update_subscription.data:
                auto_pay = update_subscription.data['auto_pay']

        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        if subscription_object.subscription_type == SUBSCRIPTION_TYPES[2][0]:
            raise api_exceptions.Conflict409(
                ErrorMessages.SUBSCRIPTION_409_UNLIMITED
            )
        if auto_pay is not None:
            subscription_object.auto_pay = auto_pay
            subscription_object.save()
        if credit:
            subscription_object.customer.credit = credit
            subscription_object.save()
        if base_balance is not None and used_balance is not None:
            if Decimal(used_balance) > Decimal(base_balance):
                raise api_exceptions.Conflict409(
                    _("Used balance can not be greater than base balance")
                )
            if BasicService.apply_base_balance(
                    subscription_object.branch.branch_code,
                    subscription_object.subscription_code,
                    base_balance,
            ):
                if BasicService.execute_topup_reset_action(
                        subscription_code,
                ):
                    BasicService.debit_balance(
                        subscription_code,
                        used_balance,
                    )

        subscription_details = cls.get_subscription_from_cgrates(
            subscription_object,
        )

        return subscription_details

    @classmethod
    def get_subscriptions_anti(cls, customer_code, request):
        """
        This duplicates get_subscriptions and it's the result of an anti
        pattern.
        @TODO: Remove this
        :param customer_code:
        :param request:
        :return:
        """
        force_reload = False
        query_params = request.query_params
        subscription_codes = SubscriptionAntiSerializer(
            data=Tools.get_dict_from_json(request.body) if request.body else {}
        )
        subscription_codes.is_valid(raise_exception=True)
        subscription_codes = subscription_codes.data
        if customer_code is not None:
            subscriptions_object = Subscription.objects.filter(
                customer__customer_code=customer_code
            )

            if not subscriptions_object:
                raise api_exceptions.Conflict409(
                    ErrorMessages.CUSTOMER_409,
                )
        else:
            subscriptions_object = Subscription.objects.all()

        if query_params is not None:
            if 'force_reload' in query_params:
                force_reload = True
            # All filters in subscriptions
            subscriptions_object = CommonService.filter_query_common(
                subscriptions_object,
                query_params,
            )

            if 'subscription_type' in query_params:
                if query_params['subscription_type'] not in (
                        FinanceConfigurations.Subscription.TYPE[0][0],
                        FinanceConfigurations.Subscription.TYPE[1][0],
                        FinanceConfigurations.Subscription.TYPE[2][0],
                ):
                    raise api_exceptions.ValidationError400(
                        {
                            'subscription_type':
                                ErrorMessages.SUBSCRIPTION_NUMBER_400
                        }
                    )
                subscriptions_object = subscriptions_object.filter(
                    subscription_type=query_params['subscription_type']
                )

            if 'number' in query_params:
                try:
                    subscriptions_object = subscriptions_object.filter(
                        number__icontains=query_params['number']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'number': ErrorMessages.SUBSCRIPTION_NUMBER_400
                        }
                    )
            if 'subscription_code' in query_params:
                try:
                    subscriptions_object = subscriptions_object.filter(
                        subscription_code__icontains=query_params[
                            'subscription_code'
                        ]
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'subscription_code':
                                ErrorMessages.SUBSCRIPTION_CODE_400
                        }
                    )
            if subscription_codes:
                subscription_codes = subscription_codes['subscription_codes']
                try:
                    subscriptions_object = subscriptions_object.filter(
                        subscription_code__in=subscription_codes
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'subscription_code':
                                ErrorMessages.SUBSCRIPTION_CODE_400
                        }
                    )
            if 'is_allocated' in query_params:
                try:
                    is_allocated = False
                    if query_params['is_allocated'] in ('True', 'true', 1):
                        is_allocated = True
                    subscriptions_object = subscriptions_object.filter(
                        is_allocated=is_allocated,
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'is_allocated': ErrorMessages.BOOLEAN_400
                        }
                    )

            # Order by
            subscriptions_object = CommonService.order_by_query(
                Subscription,
                subscriptions_object,
                query_params,
            )

        subscriptions_object, paginator = Paginator().paginate(
            request=request,
            queryset=subscriptions_object,
        )
        subscriptions_list = []
        for subscription in subscriptions_object:
            subscription_detail = cls.get_subscription_from_cgrates(
                subscription,
                force_reload,
            )
            subscriptions_list.append(subscription_detail)

        return subscriptions_list, paginator

    @classmethod
    def get_subscriptions(cls, customer_code, request):
        """
        Get all subscriptions with details
        :param customer_code:
        :param request:
        :return:
        """
        force_reload = False
        query_params = request.query_params
        if customer_code is not None:
            subscriptions_object = Subscription.objects.filter(
                customer__customer_code=customer_code
            )

            if not subscriptions_object:
                raise api_exceptions.Conflict409(
                    ErrorMessages.CUSTOMER_409,
                )
        else:
            subscriptions_object = Subscription.objects.all()

        if query_params is not None:
            if 'force_reload' in query_params:
                force_reload = True
            # All filters in subscriptions
            subscriptions_object = CommonService.filter_query_common(
                subscriptions_object,
                query_params,
            )

            if 'subscription_type' in query_params:
                if query_params['subscription_type'] not in (
                        FinanceConfigurations.Subscription.TYPE[0][0],
                        FinanceConfigurations.Subscription.TYPE[1][0],
                        FinanceConfigurations.Subscription.TYPE[2][0],
                ):
                    raise api_exceptions.ValidationError400(
                        {
                            'subscription_type':
                                ErrorMessages.SUBSCRIPTION_NUMBER_400
                        }
                    )
                subscriptions_object = subscriptions_object.filter(
                    subscription_type=query_params['subscription_type']
                )

            if 'number' in query_params:
                try:
                    subscriptions_object = subscriptions_object.filter(
                        number__icontains=query_params['number']
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'number': ErrorMessages.SUBSCRIPTION_NUMBER_400
                        }
                    )
            if 'subscription_code' in query_params:
                try:
                    subscriptions_object = subscriptions_object.filter(
                        subscription_code__icontains=query_params[
                            'subscription_code'
                        ]
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'subscription_code':
                                ErrorMessages.SUBSCRIPTION_CODE_400
                        }
                    )
            if 'subscription_codes' in query_params:
                subscription_codes = [
                    e.strip() for e in
                    query_params['subscription_codes'].split(',')
                ]
                try:
                    subscriptions_object = subscriptions_object.filter(
                        subscription_code__in=subscription_codes
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        {
                            'subscription_code':
                                ErrorMessages.SUBSCRIPTION_CODE_400
                        }
                    )
            if 'is_allocated' in query_params:
                try:
                    is_allocated = False
                    if query_params['is_allocated'] in ('True', 'true', 1):
                        is_allocated = True
                    subscriptions_object = subscriptions_object.filter(
                        is_allocated=is_allocated,
                    )
                except ValueError:
                    raise api_exceptions.ValidationError400(
                        detail={
                            'is_allocated': ErrorMessages.BOOLEAN_400
                        }
                    )

            # Order by
            subscriptions_object = CommonService.order_by_query(
                Subscription,
                subscriptions_object,
                query_params,
            )

        subscriptions_object, paginator = Paginator().paginate(
            request=request,
            queryset=subscriptions_object,
        )
        subscriptions_list = []
        for subscription in subscriptions_object:
            subscription_detail = cls.get_subscription_from_cgrates(
                subscription,
                force_reload,
            )
            subscriptions_list.append(subscription_detail)

        return subscriptions_list, paginator

    @classmethod
    def get_availability_subscription(
            cls,
            customer_code,
            subscription_code,
    ):
        """
        Get the current availability of a subscription
        :param customer_code:
        :param subscription_code:
        :return:
        """
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        subscription_cgrates = BasicService.get_account(
            subscription_object.subscription_code,
            force_reload=True,
        )
        account_details = BasicService.account_object(
            subscription_cgrates
        )

        if account_details['disabled']:
            condition = 'disable'
        else:
            condition = 'enable'

        return {
            'status_code': condition,
        }

    @classmethod
    def convert_subscription(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Convert prepaid subscription's to postpaid
        :param body:
        :param customer_code:
        :param subscription_code:
        :return:
        """
        base_balance = Tools.get_dict_from_json(body)
        convert_serializer = SubscriptionConvertSerializer(
            data=base_balance,
        )
        if convert_serializer.is_valid(raise_exception=True):
            base_balance = int(
                float(convert_serializer.data['base_balance']),
            )

        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        if subscription_object.subscription_type != SUBSCRIPTION_TYPES[1][0]:
            raise api_exceptions.Conflict409(
                _("Can not convert a non prepaid subscription to postpaid")
            )
        current_balance = BasicService.get_balance(
            subscription_object.subscription_code,
        )['current_balance_prepaid']
        try:
            # Remove base balance and thresholds related to prepaid
            BasicService.apply_base_balance(
                subscription_object.branch.branch_code,
                subscription_object.subscription_code,
                base_balance=0,
                is_prepaid=True,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)
        try:
            # Debit current prepaid balance from CGRateS
            BasicService.debit_balance(
                subscription_code,
                current_balance,
                is_prepaid=True,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)
        try:
            # Set new postpaid balance in CGRateS
            BasicService.set_balance(
                subscription_object.subscription_code,
                base_balance,
                is_prepaid=False,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)
        try:
            # Remove action plans related to prepaid balance
            BasicService.remove_action_plan_balance_expiry(
                subscription_object.subscription_code,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)
        try:
            # Add base balance and thresholds related to postpaid
            BasicService.apply_base_balance(
                subscription_object.branch.branch_code,
                subscription_object.subscription_code,
                base_balance,
                False,
                is_prepaid=False,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)
        try:
            BasicService.set_attribute_profile_account(
                subscription_object.subscription_code,
                subscription_object.number,
                SUBSCRIPTION_TYPES[0][0],
                subscription_object.branch.branch_code,
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                BranchService.get_emergency_destinations(),
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)
        # 1. Get current balance of prepaid and add to to credit
        if Decimal(current_balance) > Decimal(0):
            CustomerService.no_pay_increase_credit(
                subscription_object.customer,
                current_balance,
                _(
                    "This credit invoice is generated automatically in the "
                    "procedure of converting from prepaid to postpaid"
                )
            )
        # 3. Disable the active package invoice
        PackageInvoiceService.disable_active_package(
            subscription_object.subscription_code
        )
        # 4. Change type of subscription to postpaid
        subscription_object.subscription_type = SUBSCRIPTION_TYPES[0][0]
        subscription_object.save()

        return True

    @classmethod
    def change_base_balance_subscription(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Increase or decrease the base balance of a subscription (without
        payment)
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        base_balance = Tools.get_dict_from_json(body)
        bb_serializer = SubscriptionBaseBalanceSerializer(
            data=base_balance,
        )
        if not bb_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                bb_serializer.errors,
            )
        data = bb_serializer.data
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )

        if data['operation_type'] == \
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0]:
            cls.no_pay_decrease_base_balance(
                subscription_object,
                data['to_credit'],
                data['value'],
            )
        else:
            cls.no_pay_increase_base_balance(
                subscription_object,
                data['value'],
            )

        return True

    @classmethod
    def change_availability_subscription(
            cls,
            customer_code,
            subscription_code,
            body=''
    ):
        """
        Change the availability of a subscription
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        toggle_body = None
        if body:
            toggle_json = Tools.get_dict_from_json(body)
            toggle_body = BasicService.get_toggle_subscription(
                toggle_json,
            )
            toggle_body = toggle_body['status_code']

        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        subscription_object.updated_at = datetime.now()
        subscription_object.save()
        new_condition = True

        if toggle_body is None:
            subscription_cgrates = BasicService.get_account(
                subscription_object.subscription_code,
            )
            account_details = BasicService.account_object(
                subscription_cgrates
            )

            if account_details['disabled']:
                new_condition = False
        else:
            if toggle_body == 'enable':
                new_condition = False

        if BasicService.set_account_availability(
                subscription_object.subscription_code,
                new_condition,
        ):
            return {
                'status_code': 'disable',
                'description': _("Subscription is now disabled")

            }
        else:
            return {
                'status_code': 'enable',
                'description': _("Subscription is now enabled")
            }

    @classmethod
    def renew_branch(cls, subscription_id):
        """
        Remove old attribute profile if exists and add two new attribute
        profile based on branch code
        :param subscription_id:
        :return:
        """
        should_renew = False
        try:
            subscription_object = Subscription.objects.get(
                id=subscription_id,
            )
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.SUBSCRIPTION_404,
            )
        # 0. Renew branch id based on branches and subscription's number
        new_branch = BranchService.get_branch_from_number(
            subscription_object.number,
        )

        if new_branch.id != subscription_object.branch_id:
            subscription_object.branch_id = new_branch.id
            subscription_object.save()
            should_renew = True

        if should_renew:
            # 1. Remove old attribute profile if exists
            try:
                BasicService.remove_attribute_profile(
                    attribute_name=subscription_object.subscription_code,
                    attribute_type='None',
                )
            except (api_exceptions.APIException, api_exceptions.NotFound404):
                pass

            # 2. Renew branch based on subscription's number
            BasicService.set_attribute_profile_account(
                subscription_object.subscription_code,
                subscription_object.number,
                subscription_object.subscription_type,
                new_branch.branch_code,
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                BranchService.get_emergency_destinations(),
            )

        return True

    @classmethod
    def create_subscription(
            cls,
            customer_code,
            body,
    ):
        """
        Create a new subscription. This method is heavily relied on CGRateS.
        There are separate steps in creating a new subscription. If
        each one of them fails, the whole process breaks.
        :param customer_code:
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        customer_id = None

        if customer_code is None:
            if 'customer_code' not in body:
                raise api_exceptions.ValidationError400({
                    'customer_code': _('No customer code is found in url or '
                                       'body. you must provide one')
                })
            else:
                customer_code = body.pop("customer_code", None)
                try:
                    customer_object = Customer.objects.get(
                        customer_code=customer_code,
                    )
                    customer_id = customer_object.id
                except Customer.DoesNotExist:
                    customer_serializer = CustomerSerializer(data={
                        "customer_code": customer_code,
                    })

                    if customer_serializer.is_valid(raise_exception=True):
                        customer_serializer.save()
                        customer_id = customer_serializer.data['id']
        else:
            try:
                customer_object = Customer.objects.get(
                    customer_code=customer_code,
                )
                customer_id = customer_object.id
            except Customer.DoesNotExist:
                raise api_exceptions.NotFound404(
                    ErrorMessages.CUSTOMER_404,
                )

        if 'base_balance' not in body:
            raise api_exceptions.ValidationError400({
                'base_balance': ErrorMessages.REQUIRED_FIELD_400
            })

        is_active = True
        if 'is_active' in body:
            is_active = body.pop("is_active", None)

        body['number'] = Tools.normalize_number(
            body['number'],
        )
        if cls.is_blacklist_number(
                body['number'],
        ):
            raise api_exceptions.Conflict409(
                _("This number is blacklisted and can not be used")
            )
        base_balance = body.pop("base_balance", None)
        package_id = body.pop("package_id", None)
        credit = body.pop("credit", None)
        branch_object = BranchService.get_branch_from_number(
            body['number'],
        )
        branch_code = branch_object.branch_code
        body['branch_id'] = branch_object.id
        body['customer_id'] = customer_id
        body['subscription_type'] = cls.get_subscription_type(
            number=body['number'],
            subscription_type=
            body['subscription_type'] if 'subscription_type' in body else '',
        )
        is_prepaid = False

        if body['subscription_type'] == SUBSCRIPTION_TYPES[1][0]:
            is_prepaid = True

        subscription_serializer = SubscriptionSerializer(
            data=body,
            context=
            {
                "used_balance_postpaid": 0,
                "base_balance_postpaid": 0 if is_prepaid else base_balance,
                "current_balance_postpaid": 0 if is_prepaid else base_balance,
                "used_balance_prepaid": 0,
                "base_balance_prepaid": 0 if not is_prepaid else base_balance,
                "current_balance_prepaid": 0 if not is_prepaid else
                base_balance,
            },
        )
        if subscription_serializer.is_valid(raise_exception=True):
            subscription_serializer.save()

        subscription_object = Subscription.objects.get(
            id=subscription_serializer.data['id'],
        )

        if credit:
            CustomerService.no_pay_increase_credit(
                subscription_object.customer,
                credit,
                _(
                    "This credit invoice is generated automatically for "
                    "increasing customer's credit at subscription's creation"
                )
            )
        allow_negative = False
        if subscription_object.subscription_type == SUBSCRIPTION_TYPES[2][0]:
            allow_negative = True
            is_prepaid = None
        # 0. If it's prepaid, initialize it
        expiry_date = None
        if is_prepaid:
            try:
                if package_id:
                    package_id = Tools.uuid_validation(package_id)
                    default_package = Package.objects.get(
                        id=package_id
                    )
                else:
                    default_package = Package.objects.get(
                        package_code=
                        FinanceConfigurations.Package.DEFAULT_PACKAGE_CODE[0]
                    )
                expiry_date = CommonService.get_expired_at(
                    default_package.package_due
                )
            except Package.DoesNotExist:
                subscription_object.delete()
                raise api_exceptions.NotFound404(
                    ErrorMessages.PACKAGE_404
                )
            except api_exceptions.ValidationError400 as e:
                subscription_object.delete()
                raise api_exceptions.ValidationError400(e.detail)
            base_balance = float(default_package.package_value)
            try:
                cls.initialize_prepaid(
                    subscription_object=subscription_object,
                    expiry_date=expiry_date,
                    package_object=default_package,
                )
            except api_exceptions.APIException as e:
                subscription_object.delete()
                raise api_exceptions.APIException(e)
        # 1. Add account to CGRateS
        try:
            BasicService.set_account(
                subscription_object.subscription_code,
                is_active=is_active,
                allow_negative=allow_negative,
            )
        except api_exceptions.APIException as e:
            subscription_object.delete()
            raise api_exceptions.APIException(e)
        # 2. Set balance
        try:
            BasicService.set_balance(
                subscription_object.subscription_code,
                base_balance,
                is_prepaid=is_prepaid,
                expiry_date=expiry_date,
            )
        except api_exceptions.APIException as e:
            subscription_object.delete()
            raise api_exceptions.APIException(e)
        # 3. Apply base balance
        try:
            BasicService.apply_base_balance(
                branch_code,
                subscription_object.subscription_code,
                base_balance,
                allow_negative,
                is_prepaid=is_prepaid,
            )
        except api_exceptions.APIException as e:
            subscription_object.delete()
            raise api_exceptions.APIException(e)
        # 4. Set attribute profile for account
        try:
            BasicService.set_attribute_profile_account(
                subscription_object.subscription_code,
                subscription_object.number,
                subscription_object.subscription_type,
                branch_code,
                FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
                BranchService.get_emergency_destinations(),
            )
        except api_exceptions.APIException as e:
            subscription_object.delete()
            raise api_exceptions.APIException(e)

        return subscription_serializer.data

    @classmethod
    def add_balance_from_subscription(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Force debit from a subscription (without usage)
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        is_prepaid = True
        if subscription_object.subscription_type == SUBSCRIPTION_TYPES[0][0]:
            is_prepaid = False
        add_balance_serializer = ChangeBalanceSerializer(
            data=body,
        )
        value = None
        if add_balance_serializer.is_valid(raise_exception=True):
            value = add_balance_serializer.data['value']

        if value is not None:
            # Check for base and current balance
            balances = BasicService.get_balance(
                subscription_code,
                True,
            )
            if is_prepaid:
                base_balance = balances['base_balance_prepaid']
                current_balance = balances['current_balance_prepaid']
            else:
                base_balance = balances['base_balance_postpaid']
                current_balance = balances['current_balance_postpaid']
            if int(value) + int(current_balance) >= int(base_balance):
                value = int(base_balance) - int(current_balance)
            if BasicService.add_balance(
                    subscription_code,
                    value,
                    is_prepaid,
            ):
                BasicService.renew_thresholds(
                    subscription_object.branch.branch_code,
                    subscription_object.subscription_code,
                    base_balance,
                    int(value) + int(current_balance),
                    is_prepaid,
                )
                return {
                    'subscription_code': subscription_code,
                    'add': value,
                }

    @classmethod
    def debit_balance_from_subscription(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Force debit from a subscription (without usage)
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        body = Tools.get_dict_from_json(body)
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        is_prepaid = True
        if subscription_object.subscription_type == SUBSCRIPTION_TYPES[0][0]:
            is_prepaid = False
        debit_balance_serializer = ChangeBalanceSerializer(
            data=body,
        )
        value = None
        if debit_balance_serializer.is_valid(raise_exception=True):
            value = debit_balance_serializer.data['value']

        if value is not None:
            # Check for base and current balance
            balances = BasicService.get_balance(
                subscription_code,
                True,
            )
            if is_prepaid:
                current_balance = balances['current_balance_prepaid']
            else:
                current_balance = balances['current_balance_postpaid']
            if int(current_balance) - int(value) < 0:
                value = int(current_balance)
            if BasicService.debit_balance(
                    subscription_code,
                    value,
                    is_prepaid,
            ):
                return {
                    'subscription_code': subscription_code,
                    'debit': value,
                }

    @classmethod
    def deallocate_subscription(
            cls,
            customer_code,
            subscription_code,
            body,
    ):
        """
        Deallocate a subscription (Remove attributes in CGRateS)
        :param customer_code:
        :param subscription_code:
        :param body:
        :return:
        """
        if body:
            body = Tools.get_dict_from_json(body)
            cause = SubscriptionDeallocationSerializer(data=body)
            if not cause.is_valid():
                raise api_exceptions.ValidationError400(
                    cause.errors,
                )
            cause = cause.data['cause']
        else:
            cause = FinanceConfigurations.Subscription.DEALLOCATION_CAUSE[0][0]

        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )
        print('my2')
        print(subscription_object)
        if BasicService.set_account_availability(
                subscription_object.subscription_code,
                True,
        ):
            subscription_object.deallocate(cause)
            if BasicService.remove_attribute_profile(
                    attribute_name=subscription_object.subscription_code,
                    attribute_type=
                    BasicConfigurations.Types.ATTRIBUTE_TYPE[0][0],
            ):
                BasicService.remove_action_plan_balance_expiry(
                    subscription_object.subscription_code,
                )
                return cls.get_subscription_from_cgrates(
                    subscription_object,
                )

        raise api_exceptions.APIException(
            _('Can not deallocate subscription due to Service problems')
        )

    @classmethod
    def remove_subscription(
            cls,
            customer_code=None,
            subscription_code=None,
    ):
        """
        Remove a subscription completely (Use with cautious)
        :param customer_code:
        :param subscription_code:
        :return:
        """
        subscription_object = CommonService.get_subscription_object(
            customer_code=customer_code,
            subscription_code=subscription_code,
        )

        if BasicService.remove_account(
                subscription_object.subscription_code,
        ):
            # Remove attribute profile after removal
            if BasicService.remove_attribute_profile(
                    attribute_name=subscription_object.subscription_code,
                    attribute_type=
                    BasicConfigurations.Types.ATTRIBUTE_TYPE[0][0],
            ):
                BasicService.remove_thresholds(
                    subscription_object.subscription_code,
                    True,
                )
                BasicService.remove_thresholds(
                    subscription_object.subscription_code,
                    False,
                )
                BasicService.remove_action_plan_balance_expiry(
                    subscription_object.subscription_code,
                )
                BasicService.remove_actions(
                    [
                        CGRatesConventions.topup_reset_action(
                            subscription_object.subscription_code,
                            True,
                        ),
                        CGRatesConventions.topup_reset_action(
                            subscription_object.subscription_code,
                            False,
                        )
                    ]
                )
                subscription_object.delete()

                return True

        raise api_exceptions.APIException(
            _('Can not delete subscription due to Service problems')
        )

    @classmethod
    def get_subscription_type(cls, number, subscription_type=''):
        """
        Return subscription type based on number from
        FinanceConfigurations.Subscription.TYPE
        :param subscription_type:
        :param number: normalized number of subscription
        :return: str
        """
        destination_object = Destination.objects.annotate(reverse_number=Value(
            number,
            output_field=CharField(),
        )).filter(
            reverse_number__istartswith=F('prefix'),
            name=FinanceConfigurations.Destination.CORPORATE_DEFAULT_NAME[1],
            code=FinanceConfigurations.Destination.CODE_CHOICES[1][0],
        )
        if destination_object.count() == 0:
            return SUBSCRIPTION_TYPES[2][0]

        if subscription_type == '' or subscription_type != \
                SUBSCRIPTION_TYPES[1][0]:
            return SUBSCRIPTION_TYPES[0][0]

        return SUBSCRIPTION_TYPES[1][0]

    @classmethod
    def renew_subscription_type(cls, subscription_id):
        """
        Add/Remove thresholds if necessary
        profile based on branch code
        :param subscription_id:
        :return:
        """
        should_renew = False
        try:
            subscription_object = Subscription.objects.get(
                id=subscription_id,
            )
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                ErrorMessages.SUBSCRIPTION_404,
            )

        new_type = cls.get_subscription_type(
            subscription_object.number,
            subscription_object.subscription_type,
        )

        if new_type != subscription_object.subscription_type:
            subscription_object.subscription_type = new_type
            subscription_object.save()
            should_renew = True

        if subscription_object.branch is None:
            subscription_object.branch = BranchService.get_branch_from_number(
                subscription_object.number,
            )
            subscription_object.save()

        # Emergency numbers may has been changed
        BasicService.set_attribute_profile_account(
            subscription_object.subscription_code,
            subscription_object.number,
            new_type,
            subscription_object.branch.branch_code,
            FinanceConfigurations.Branch.DEFAULT_EMERGENCY_BRANCH[0],
            BranchService.get_emergency_destinations(),
        )

        if should_renew:
            if new_type == SUBSCRIPTION_TYPES[0][0]:
                # Change allow negative
                BasicService.set_account(
                    account_name=subscription_object.subscription_code,
                    allow_negative=False,
                    is_active=None,
                )
                # Renew thresholds
                base_balance = BasicService.get_base_balance_postpaid(
                    subscription_code=subscription_object.subscription_code,
                    force_reload=True,
                )

                if BasicService.execute_topup_reset_action(
                        subscription_object.subscription_code,
                ):
                    BasicService.renew_thresholds(
                        subscription_object.branch.branch_code,
                        subscription_object.subscription_code,
                        base_balance,
                        base_balance,
                        False,
                    )
            else:
                # Change allow negative
                BasicService.set_account(
                    account_name=subscription_object.subscription_code,
                    allow_negative=True,
                    is_active=None,
                )
                # Remove thresholds
                BasicService.remove_thresholds(
                    subscription_object.subscription_code,
                    False,
                )

        return True

    @classmethod
    def initialize_prepaid(
            cls,
            subscription_object,
            package_object,
            expiry_date,
    ):
        """
        Initialize a prepaid subscription. This method creates the first
        PackageInvoice for a prepaid subscription
        :param subscription_object:
        :param package_object:
        :param expiry_date:
        :return:
        """
        try:
            package_invoice_object = PackageInvoice()
            package_invoice_object.subscription = subscription_object
            package_invoice_object.expired_at = expiry_date
            package_invoice_object.is_active = True
            package_invoice_object.auto_renew = True
            package_invoice_object.total_value = package_object.package_value
            package_invoice_object.total_cost = package_object.package_price
            package_invoice_object.updated_status_at = datetime.now()
            package_invoice_object.package = package_object
            package_invoice_object.credit_invoice = None
            package_invoice_object.description = _(
                "This invoice is created automatically for initialization of "
                "a prepaid account"
            )
            package_invoice_object.status_code = \
                FinanceConfigurations.Invoice.STATE_CHOICES[2][0]
            package_invoice_object.save()

            return True
        except Exception as e:
            raise api_exceptions.APIException(e)

    @classmethod
    def no_pay_increase_base_balance(
            cls,
            subscription_object,
            value,
    ):
        """
        Increase subscription's base balance without payment
        :param subscription_object:
        :param value:
        :return:
        """
        bb_dict = {
            "subscription_id": subscription_object.id,
            "total_cost": value,
            "operation_type":
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[0][0],
            "description": _(
                "This base balance invoice is generated automatically for "
                "increasing subscription's base balance without payment",
            )
        }
        bb_serializer = BaseBalanceInvoiceSerializer(data=bb_dict)
        if not bb_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                bb_serializer.errors,
            )

        with transaction.atomic():
            BaseBalanceInvoiceService.check_latest_invoice(
                subscription_object=subscription_object,
                operation_type=bb_serializer.validated_data['operation_type'],
            )
            bb_serializer.save()

            CustomerService.no_pay_increase_credit(
                subscription_object.customer,
                bb_serializer.data['total_cost'],
                _(
                    "This credit invoice is generated automatically for "
                    "increasing subscription's base balance without payment"
                ),
                used_for=FinanceConfigurations.CreditInvoice.USED_FOR[1][0],
                used_for_id=bb_serializer.data['id'],
            )

    @classmethod
    def no_pay_decrease_base_balance(
            cls,
            subscription_object,
            to_credit,
            value,
    ):
        """
        Decrease subscription's base balance without payment
        :param subscription_object:
        :param to_credit:
        :param value:
        :return:
        """
        bb_dict = {
            "subscription_id": subscription_object.id,
            "total_cost": value,
            "operation_type":
                FinanceConfigurations.CreditInvoice.OPERATION_TYPES[1][0],
            "to_credit": to_credit
        }
        bb_serializer = BaseBalanceInvoiceSerializer(data=bb_dict)
        if not bb_serializer.is_valid():
            raise api_exceptions.ValidationError400(
                bb_serializer.errors,
            )
        balance_details = BasicService.get_balance(
            subscription_code=subscription_object.subscription_code,
            force_reload=True,
        )
        current_base = Decimal(
            balance_details['base_balance_postpaid']
        )
        current_balance = Decimal(
            balance_details['current_balance_postpaid']
        )
        if Decimal(bb_serializer.validated_data['total_cost']) > Decimal(
                current_base
        ):
            raise api_exceptions.ValidationError400({
                'value': ErrorMessages.BASE_BALANCE_INVOICE_409,
            })
        if Decimal(bb_serializer.validated_data['total_cost']) > Decimal(
                current_balance
        ):
            raise api_exceptions.ValidationError400({
                'value': ErrorMessages.BASE_BALANCE_INVOICE_409_CURRENT,
            })
        bb_serializer.save()
        BasicService.decrease_base_postpaid(
            subscription_object.branch.branch_code,
            subscription_object.subscription_code,
            bb_serializer.data['total_cost'],
        )
        if to_credit:
            # Increase credit after decreasing base balance
            CustomerService.no_pay_increase_credit(
                subscription_object.customer,
                bb_serializer.data['total_cost'],
                _(
                    "This credit invoice is generated automatically for "
                    "increasing customer's credit after decreasing it's "
                    "base balance"
                )
            )

        return True

    @classmethod
    def is_blacklist_number(cls, number):
        """
        Check for blacklisted number based on RuntimeConfig
        :param number:
        :return:
        """
        days = int(
            RuntimeConfigService.get_value(
                FinanceConfigurations.RuntimeConfig.KEY_CHOICES[9][0],
            )
        )

        if Subscription.objects.filter(
                number=number,
                is_allocated=False,
                deallocation_cause=FinanceConfigurations.Subscription
                        .DEALLOCATION_CAUSE[1][0],
                deallocated_at__gt=(datetime.now() - timedelta(days=days))
        ):
            return True

        return False
