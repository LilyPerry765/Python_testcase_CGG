# --------------------------------------------------------------------------
# All similar API calls to CGRateS that have weigh must consider the
# chronological order of applying. This is an important rule specially in
# setting up AttributeS
# (C) 2019 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - base_services.py
# Created at 2019-12-22,  12:10:53
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
import uuid as uuid
from datetime import datetime
from decimal import Decimal

import math
import requests
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework import exceptions, status

from cgg.apps.basic.apps import BasicConfig
from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.apps.basic.versions.v1.config.cgrates_conventions import (
    CGRatesConventions
)
from cgg.apps.basic.versions.v1.config.cgrates_methods import (
    CGRatesMethods
)
from cgg.apps.basic.versions.v1.serializers.cgrates import (
    AccountSerializer,
    ActionsV1Serializer,
    ActionsV2Serializer,
    ActiveSessionsV1Serializer,
    AttributeProfileSerializer,
    BalanceSerializer,
    CDRMinimalSerializer,
    CDRSerializer,
    ChargerProfileSerializer,
    DestinationRateSerializer,
    DestinationSerializer,
    FilterSerializer,
    RateSerializer,
    RatingPlanSerializer,
    RatingProfileSerializer,
    SupplierProfileSerializer,
    ThresholdProfileSerializer,
    TimingSerializer,
    ToggleSubscriptionSerializer,
)
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core import api_exceptions
from cgg.core.cache import Cache
from cgg.core.requests import Requests


class BasicService:
    """
    Access to CGRateS through API calls.
    This class is heavily related to CGRateS conventions.
    """

    @classmethod
    def __get_response(
            cls,
            method,
            body,
            recovery=False,
            timeout=settings.CGG['SERVICE_TIMEOUT'],
    ):
        """
        Generic method to create a request and return response from CGRateS
        :param recovery: Check if this is timeout recovery or not
        :param timeout: Default value from settings, could be overwritten
        :param method: str -> Subsystem.MethodName (Use cgrates_methods.py)
        :param body: dict to convert to JSON
        :return:
        """
        cgr_auth = settings.CGG['AUTH_TOKENS']['CGRATES_BASIC_AUTHENTICATION']
        url = settings.CGG['BASE_URLS']['CGRATES']
        request_id = uuid.uuid4().hex
        params = {
            "id": request_id,
            "jsonrpc": "2.0",
            "method": method,
            "params": body,
        }
        try:
            res = Requests.post(
                app_name=BasicConfig.name,
                label=method,
                url=url,
                json=params,
                headers={
                    'Content-type': 'application/json',
                },
                timeout=timeout,
                auth=(
                    cgr_auth['USERNAME'],
                    cgr_auth['PASSWORD'],
                )
            )
        except requests.exceptions.ConnectionError:
            raise api_exceptions.APIException(
                _("Connection error"),
            )
        except requests.exceptions.Timeout:
            if not recovery:
                return cls.__get_response(
                    method,
                    body,
                    recovery=True,
                    timeout=timeout,
                )
            raise api_exceptions.TimeOut408(_("Timeout on connection"))
        except exceptions.APIException as e:
            raise api_exceptions.raise_exception(
                e.status_code,
                e.detail,
            )

        if res.status_code == status.HTTP_401_UNAUTHORIZED:
            raise api_exceptions.AuthenticationFailed401()
        data = res.json()
        if data['id'] != request_id:
            raise api_exceptions.ValidationError400(
                detail={
                    'non_fields': _(
                        "The id of the request is not configured correctly"
                    )
                },
            )
        if data['error']:
            # Hardcoded due to limitation of JSON-RPC implementation in Go
            # (CGRateS)
            if data['error'] in (
                    'NOT_FOUND',
                    'SERVER_ERROR: NOT_FOUND',
            ):
                raise api_exceptions.NotFound404(
                    data['error'],
                )
            raise api_exceptions.APIException(
                data['error'],
            )

        return data['result']

    @classmethod
    def delete_subscription_related_cache(cls, subscription_code):
        """
        Remove all caches related to a subscription
        :param subscription_code:
        """
        Cache.delete(
            key=Cache.KEY_CONVENTIONS['base_balance_postpaid'],
            values={
                'subscription_code': subscription_code,
            },
        )
        Cache.delete(
            key=Cache.KEY_CONVENTIONS['base_balance_prepaid'],
            values={
                'subscription_code': subscription_code,
            },
        )
        Cache.delete(
            key=Cache.KEY_CONVENTIONS['account_details'],
            values={
                'subscription_code': subscription_code,
            },
        )

    @classmethod
    def ping(cls):
        """
        :return: Ping CGRateS APIerS
        """
        method = CGRatesMethods.ping()
        body = [
            {
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.APIException:
            return False

        return True

    @classmethod
    def get_account(cls, subscription_code, force_reload=False):
        """
        :param force_reload: Delete cached value
        :param subscription_code:
        :return: dict details of account
        """
        if force_reload:
            cls.delete_subscription_related_cache(subscription_code)

        account_details = Cache.get(
            key=Cache.KEY_CONVENTIONS['account_details'],
            values={
                'subscription_code': subscription_code,
            },
        )

        if not account_details:
            method = CGRatesMethods.get_account()
            body = [
                {
                    "Tenant": CGRatesConventions.default_tenant(),
                    "Account": CGRatesConventions.account_name(
                        account_name=subscription_code,
                        account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][
                            0],
                    ),
                }
            ]
            try:
                account_details = cls.__get_response(method, body)
                Cache.set(
                    key=Cache.KEY_CONVENTIONS['account_details'],
                    values={
                        'subscription_code': subscription_code,
                    },
                    store_value=account_details,
                    expiry_time=
                    settings.CGG['CACHE_EXPIRY_OBJECTS'],
                )
            except api_exceptions.NotFound404:
                raise api_exceptions.NotFound404(_(
                    'Subscription {subscription_code} does not exists'.format(
                        subscription_code=subscription_code,
                    )
                ))
            except api_exceptions.APIException:
                raise api_exceptions.APIException(
                    _('Something went wrong in the request to CGRateS')
                )

        return account_details

    @classmethod
    def get_balance(
            cls,
            subscription_code,
            force_reload=False,
    ):
        print('account_details_cgrates')
        account_details_cgrates = cls.get_account(
            subscription_code,
            force_reload,
        )
        balances = cls.balances_object(account_details_cgrates)
        balance_prepaid = None
        balance_postpaid = None
        has_balance = False

        for balance in balances:
            if balance['id'] == CGRatesConventions.balance_postpaid():
                balance_postpaid = balance
                has_balance = True
            if balance['id'] == CGRatesConventions.balance_prepaid():
                balance_prepaid = balance
                has_balance = True

        if has_balance:
            current_balance_prepaid = int(
                float(balance_prepaid['value']),
            )
            base_balance_prepaid = cls.get_base_balance_prepaid(
                subscription_code,
                force_reload
            )
            usage_prepaid = base_balance_prepaid - current_balance_prepaid
            current_balance_postpaid = int(
                float(balance_postpaid['value']),
            )
            base_balance_postpaid = cls.get_base_balance_postpaid(
                subscription_code,
                force_reload,
            )
            usage_postpaid = base_balance_postpaid - current_balance_postpaid
            if int(usage_prepaid) < 0:
                usage_prepaid = 0
            if int(usage_postpaid) < 0:
                usage_postpaid = 0
            return {
                "used_balance_postpaid": usage_postpaid,
                "used_balance_prepaid": usage_prepaid,
                "base_balance_postpaid": base_balance_postpaid,
                "base_balance_prepaid": base_balance_prepaid,
                "current_balance_postpaid": current_balance_postpaid,
                "current_balance_prepaid": current_balance_prepaid,
            }

        return False

    @classmethod
    def get_accounts(
            cls,
            account_ids=None,
            limit=None,
            offset=None
    ):
        """
        :return: list of accounts
        """
        if account_ids is None:
            account_ids = []

        method = CGRatesMethods.get_accounts()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "AccountIds": account_ids,
                "Limit": limit,
                "Offset": offset,
            }
        ]
        accounts_object = cls.__get_response(method, body)

        return accounts_object

    @classmethod
    def get_base_balance_prepaid(
            cls,
            subscription_code,
            force_reload=False,
    ):
        """
        :param force_reload:
        :param subscription_code:
        :return: Decimal base balance of account
        """
        if force_reload:
            cls.delete_subscription_related_cache(subscription_code)

        base_balance_value = Cache.get(
            key=Cache.KEY_CONVENTIONS['base_balance_prepaid'],
            values={
                'subscription_code': subscription_code,
            },
        )

        if not base_balance_value:
            method = CGRatesMethods.get_actions_v1()
            body = [
                CGRatesConventions.topup_reset_action(
                    subscription_code,
                    True,
                )
            ]
            # Get base balance of subject using topup_reset actions value
            try:
                base_balance_cgrates = cls.__get_response(method, body)
            except api_exceptions.APIException:
                base_balance_cgrates = None

            if base_balance_cgrates is None:
                base_balance_value = int(0)
            else:
                base_balance = ActionsV1Serializer(
                    data=base_balance_cgrates,
                    many=True,
                )

                if not base_balance.is_valid():
                    raise api_exceptions.ValidationError400(
                        base_balance.errors
                    )

                base_balance = base_balance.data[0]
                base_balance_value = int(float(base_balance['value']))

            Cache.set(
                key=Cache.KEY_CONVENTIONS['base_balance_prepaid'],
                values={
                    'subscription_code': subscription_code,
                },
                store_value=base_balance_value,
            )

        return base_balance_value

    @classmethod
    def get_base_balance_postpaid(
            cls,
            subscription_code,
            force_reload=False,
    ):
        """
        :param force_reload:
        :param subscription_code:
        :return: Decimal base balance of account
        """
        if force_reload:
            cls.delete_subscription_related_cache(subscription_code)

        base_balance_value = Cache.get(
            key=Cache.KEY_CONVENTIONS['base_balance_postpaid'],
            values={
                'subscription_code': subscription_code,
            },
        )

        if not base_balance_value:
            method = CGRatesMethods.get_actions_v1()
            body = [
                CGRatesConventions.topup_reset_action(
                    subscription_code,
                    False,
                )
            ]
            # Get base balance of subject using topup_reset actions value
            try:
                base_balance_cgrates = cls.__get_response(method, body)
            except api_exceptions.APIException:
                base_balance_cgrates = None

            if base_balance_cgrates is None:
                base_balance_value = int(0)
            else:
                base_balance = ActionsV1Serializer(
                    data=base_balance_cgrates,
                    many=True,
                )

                if not base_balance.is_valid():
                    raise api_exceptions.ValidationError400(
                        base_balance.errors
                    )

                base_balance = base_balance.data[0]
                base_balance_value = int(float(base_balance['value']))

            Cache.set(
                key=Cache.KEY_CONVENTIONS['base_balance_postpaid'],
                values={
                    'subscription_code': subscription_code,
                },
                store_value=base_balance_value,
            )

        return base_balance_value

    @classmethod
    def set_topup_reset_action(
            cls,
            subscription_code,
            amount,
            is_prepaid=False
    ):
        """
        Never use this method directly. Use cgrates_apply_new_base_balance
        :param is_prepaid:
        :param subscription_code:
        :param amount: the amount of topup_reset (base balance)
        :return: bool True if succeed
        """
        balance_id = CGRatesConventions.balance_postpaid()
        action_id = CGRatesConventions.topup_reset_action(
            subscription_code,
            False
        )
        if is_prepaid:
            balance_id = CGRatesConventions.balance_prepaid()
            action_id = CGRatesConventions.topup_reset_action(
                subscription_code,
                True
            )
        cls.delete_subscription_related_cache(subscription_code)
        method = CGRatesMethods.set_actions()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ActionsId": action_id,
                "Overwrite": True,
                "Actions": [
                    {
                        "Identifier": "*topup_reset",
                        "BalanceID": balance_id,
                        "BalanceType": CGRatesConventions.balance_monetary(),
                        "Categories": "out",
                        "BalanceWeight": "0",
                        "Units": str(amount),
                        "ExpiryTime": "*unlimited",
                        "Weight": BasicConfigurations.Priority.CRITICAL,
                    }
                ]
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_call_url_action(cls, name, url):
        """
        Never use this method directly. Use cgrates_set_call_url_action_80
        or cgrates_set_call_url_action_100
        :param name: This arg must use CGRateSConventions
        :param url: Absolute url (This method does not validate url)
        :return: bool True if succeed
        """
        method = CGRatesMethods.set_actions()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ActionsId": CGRatesConventions.call_url_action(
                    name,
                ),
                "Overwrite": True,
                "Actions": [
                    {
                        "Identifier":
                            CGRatesConventions.call_url_action_name(),
                        "ExtraParameters": str(url),
                        "ExpiryTime": "*unlimited",
                        "Weight": BasicConfigurations.Priority.NORMAL,
                    }
                ]
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_call_url_action_expiry(
            cls,
            subscription_code,
            action_name,
    ):
        """
        :return: bool True if succeed
        """
        try:
            base_url = settings.CGG["BASE_URLS"][
                "CGRATES_GATEWAY"].strip("/")
            relative_url = reverse('cgrates_expiry', kwargs={
                "subscription_code": subscription_code,
            }).strip("/")
        except Exception as e:
            raise api_exceptions.APIException(e)

        cls.set_call_url_action(
            name=action_name,
            url=f"{base_url}/{relative_url}/"
        )

        return CGRatesConventions.call_url_action(
            action_name,
        )

    @classmethod
    def set_call_url_action_80(cls):
        """
        :return: bool True if succeed
        """
        try:
            base_url = settings.CGG["BASE_URLS"][
                "CGRATES_GATEWAY"].strip("/")
            relative_url = reverse('cgrates_notification', kwargs={
                "notify_type":
                    FinanceConfigurations.Notify.PostpaidEightyPercent,
            }).strip("/")
            prepaid_relative_url = reverse('cgrates_notification', kwargs={
                "notify_type":
                    FinanceConfigurations.Notify.PrepaidEightyPercent,
            }).strip("/")
        except Exception as e:
            raise api_exceptions.APIException(e)

        cls.set_call_url_action(
            name=CGRatesConventions.notif_80_percent_prepaid(),
            url=f"{base_url}/{prepaid_relative_url}/"
        )

        cls.set_call_url_action(
            name=CGRatesConventions.notif_80_percent_postpaid(),
            url=f"{base_url}/{relative_url}/"
        )

        return True

    @classmethod
    def set_call_url_action_100(cls):
        """
        :return: bool True if succeed
        """
        try:
            base_url = settings.CGG["BASE_URLS"][
                "CGRATES_GATEWAY"].strip("/")
            relative_url = reverse('cgrates_notification', kwargs={
                "notify_type": FinanceConfigurations.Notify.PostpaidMaxUsage,
            }).strip("/")
            prepaid_relative_url = reverse('cgrates_notification', kwargs={
                "notify_type": FinanceConfigurations.Notify.PrepaidMaxUsage,
            }).strip("/")
        except Exception as e:
            raise api_exceptions.APIException(e)

        cls.set_call_url_action(
            name=CGRatesConventions.notif_100_percent_prepaid(),
            url=f"{base_url}/{prepaid_relative_url}/"
        )
        cls.set_call_url_action(
            name=CGRatesConventions.notif_100_percent_postpaid(),
            url=f"{base_url}/{relative_url}/"
        )

    @classmethod
    def remove_thresholds(
            cls,
            subscription_code,
            is_prepaid,
    ):
        """
        Remove all thresholds of a subscription
        :param is_prepaid:
        :param subscription_code:
        :return:
        """
        # Renew thresholds
        if cls.remove_threshold_profile_80_percent(
                subscription_code,
                is_prepaid
        ) and cls.remove_threshold_profile_100_percent(
            subscription_code,
            is_prepaid
        ):
            return True

    @classmethod
    def increase_base_postpaid(
            cls,
            branch_code,
            subscription_code,
            increase_amount,
    ):
        """
        Increase base balance and current balance of postpaid balance in
        CGRateS
        :param branch_code:
        :param subscription_code:
        :param increase_amount:
        :return:
        """
        current_base_balance = cls.get_base_balance_postpaid(
            subscription_code,
            True,
        )
        new_base_balance = Decimal(increase_amount) + Decimal(
            current_base_balance,
        )

        # 1. Add new value to account
        if cls.add_balance(
                subscription_code,
                increase_amount,
                is_prepaid=False,
        ):
            # 2. Renew base balance
            if cls.apply_base_balance(
                    branch_code,
                    subscription_code,
                    new_base_balance,
                    is_prepaid=False,
            ):
                return True

        return False

    @classmethod
    def decrease_base_postpaid(
            cls,
            branch_code,
            subscription_code,
            decrease_amount,
    ):
        """
        Decrease base balance and current balance of postpaid balance in
        CGRateS
        :param branch_code:
        :param subscription_code:
        :param decrease_amount:
        :return:
        """
        balance_details = cls.get_balance(
            subscription_code=subscription_code,
            force_reload=True,
        )
        current_base_balance = Decimal(
            balance_details['base_balance_postpaid']
        )
        current_balance = Decimal(
            balance_details['current_balance_postpaid']
        )
        new_base_balance = current_base_balance - Decimal(decrease_amount)
        if cls.apply_base_balance(
                branch_code,
                subscription_code,
                new_base_balance,
                is_prepaid=False,
        ):
            decrease_amount = current_base_balance - new_base_balance
            if decrease_amount > current_balance:
                decrease_amount = current_balance
            cls.debit_balance(
                subscription_code,
                decrease_amount,
                is_prepaid=False,
            )

            return True

        return False

    @classmethod
    def renew_thresholds(
            cls,
            branch_code,
            subscription_code,
            base_balance,
            balance,
            is_prepaid,
    ):
        """
        Renew thresholds if current balance is less than 20 percent of balance
        :param is_prepaid:
        :param branch_code:
        :param subscription_code:
        :param base_balance:
        :param balance:
        :return:
        """
        if balance > base_balance:
            cls.execute_topup_reset_action(
                subscription_code,
                is_prepaid,
            )

        if int(base_balance) == int(0):
            # Remove thresholds
            cls.remove_thresholds(
                subscription_code,
                is_prepaid,
            )
            return True

        base_balance_20_percent = math.floor(
            (Decimal(base_balance) * Decimal(20)) / Decimal(100)
        )

        if Decimal(base_balance_20_percent) <= Decimal(balance):
            # Get maximum branch rate
            maximum_rate = cls.get_branch_maximum_rate(branch_code)
            # Double check 20 percent
            if Decimal(base_balance_20_percent) <= Decimal(maximum_rate):
                base_balance_20_percent = Decimal(
                    base_balance_20_percent
                ) + Decimal(maximum_rate)
            # Renew thresholds
            if cls.set_threshold_profile_80_percent(
                    subscription_code,
                    base_balance_20_percent,
                    maximum_rate,
                    is_prepaid,
            ) and cls.set_threshold_profile_100_percent(
                subscription_code,
                maximum_rate,
                is_prepaid,
            ):
                return True

    @classmethod
    def apply_base_balance(
            cls,
            branch_code,
            subscription_code,
            base_balance,
            allow_negative=False,
            is_prepaid=False,
    ):
        # Set new base balance
        cls.set_topup_reset_action(
            subscription_code,
            base_balance,
            is_prepaid,
        )
        # Set threshold if subscription is postpaid/prepaid
        # According to FinanceConfigurations.Subscription.TYPE
        if allow_negative:
            return True

        if cls.renew_thresholds(
                branch_code,
                subscription_code,
                base_balance,
                base_balance,
                is_prepaid,
        ):
            return True

        return False

    @classmethod
    def execute_topup_reset_action(
            cls,
            account_name,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
            is_prepaid=False,
    ):
        """
        :param is_prepaid:
        :param account_name:
        :param account_type:
        :return: bool True if succeed
        """
        method = CGRatesMethods.execute_action()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=account_name,
                    account_type=account_type,
                ),
                "ActionsId": CGRatesConventions.topup_reset_action(
                    account_name,
                    is_prepaid,
                ),
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_balance(
            cls,
            subscription_code,
            is_prepaid,
    ):
        """
        Add balance to *original or *incremental based on is_prepaid
        :param is_prepaid:
        :param subscription_code:
        :return: bool True if succeed
        """
        balance_id = CGRatesConventions.balance_postpaid()
        if is_prepaid:
            balance_id = CGRatesConventions.balance_prepaid()

        method = CGRatesMethods.remove_balance()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                ),
                "BalanceId": balance_id,
                "BalanceType": CGRatesConventions.balance_monetary(),
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.APIException:
            pass

        return True

    @classmethod
    def add_balance(
            cls,
            subscription_code,
            amount,
            is_prepaid,
    ):
        """
        Add balance to *original or *incremental based on is_prepaid
        :param is_prepaid:
        :param subscription_code:
        :param amount: the amount to add
        :return: bool True if succeed
        """
        balance_id = CGRatesConventions.balance_postpaid()
        if is_prepaid:
            balance_id = CGRatesConventions.balance_prepaid()

        cls.delete_subscription_related_cache(subscription_code)
        method = CGRatesMethods.add_balance()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                ),
                "BalanceType": CGRatesConventions.balance_monetary(),
                "Balance": {
                    "Value": float(amount),
                    "ID": balance_id,
                },
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_filter(
            cls,
            subscription_code,
            rules,
    ):
        """
        :param subscription_code:
        :param rules: list of dicts in this format:
            [
                {
                    "Type": "*string",
                    "FieldName": "~*req.EventType",
                    "Values": ["BalanceUpdate"]
                },
            ]
        :return: bool True if succeed
        """
        method = CGRatesMethods.set_filter()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": CGRatesConventions.filter(
                    subscription_code,
                    CGRatesConventions.notif_80_percent_postpaid(),
                ),
                "Rules": rules,
                "ActivationInterval":
                    {
                        "ActivationTime": None,
                        "ExpiryTime": None
                    }
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_threshold_profile(
            cls,
            threshold_id,
    ):
        """
        Do not use this method independently
        :param threshold_id: in CGRatesConventions.threshold format
        :return: bool True if succeed
        """
        method = CGRatesMethods.remove_threshold_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": threshold_id,
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.NotFound404:
            pass

        return True

    @classmethod
    def set_threshold_profile(
            cls,
            threshold_id,
            filter_ids,
            action_id,
    ):
        """
        Do not use this method independently
        :param threshold_id: in CGRatesConventions.threshold format
        :param action_id: in CGRatesConventions.call_url_action format
        :param filter_ids: list of strings in a format that CGRateS
        Understands:
            ["type:field:value",] e.g.
            ["*string:~*req.Account:00982191079731",]
        :return: bool True if succeed
        """
        method = CGRatesMethods.set_threshold_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": threshold_id,
                "FilterIDs": filter_ids,
                "MaxHits": 1,
                "MinHits": 0,
                "MinSleep": 0,
                "Blocker": False,
                "Weight": BasicConfigurations.Priority.HIGH,
                "ActivationInterval": {
                    "ActivationTime": None,
                    "ExpiryTime": None
                },
                "ActionIDs": [action_id, ],
                "Async": True
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_threshold_profile_80_percent(
            cls,
            subscription_code,
            is_prepaid,
    ):
        """
        :param is_prepaid:
        :param subscription_code:
        :return: bool True if succeed
        """
        notif_name = CGRatesConventions.notif_80_percent_postpaid()
        if is_prepaid:
            notif_name = CGRatesConventions.notif_80_percent_prepaid()
        threshold_id = CGRatesConventions.threshold(
            subscription_code,
            notif_name,
        )

        return cls.remove_threshold_profile(
            threshold_id=threshold_id,
        )

    @classmethod
    def remove_threshold_profile_100_percent(
            cls,
            subscription_code,
            is_prepaid,
    ):
        """
        :param is_prepaid:
        :param subscription_code:
        :return: bool True if succeed
        """
        notif_name = CGRatesConventions.notif_100_percent_postpaid()
        if is_prepaid:
            notif_name = CGRatesConventions.notif_100_percent_prepaid()
        threshold_id = CGRatesConventions.threshold(
            subscription_code,
            notif_name,
        )

        return cls.remove_threshold_profile(
            threshold_id=threshold_id,
        )

    @classmethod
    def set_threshold_profile_80_percent(
            cls,
            subscription_code,
            base_balance_20_percent,
            maximum_rate,
            is_prepaid=False,
    ):
        """
        :param is_prepaid:
        :param subscription_code:
        :param base_balance_20_percent: 20 percent of base balance (concrete)
        :param maximum_rate: Should be greater than this
        :return: bool True if succeed
        """
        notif_name = CGRatesConventions.notif_80_percent_postpaid()
        balance_id = CGRatesConventions.balance_postpaid()
        if is_prepaid:
            balance_id = CGRatesConventions.balance_prepaid()
            notif_name = CGRatesConventions.notif_80_percent_prepaid()
        account_name = CGRatesConventions.account_name(
            account_name=subscription_code,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
        )
        filter_ids = [
            f"*string:~*req.Account:{account_name}",
            "*string:~*req.EventType:BalanceUpdate",
            f"*string:~*req.BalanceID:{balance_id}",
            f"*lte:~*req.Units:{str(base_balance_20_percent)}",
            f"*gte:~*req.Units:{str(maximum_rate)}",
        ]
        threshold_id = CGRatesConventions.threshold(
            subscription_code,
            notif_name,
        )
        action_id = CGRatesConventions.call_url_action(
            notif_name,
        )

        return cls.set_threshold_profile(
            threshold_id=threshold_id,
            filter_ids=filter_ids,
            action_id=action_id,
        )

    @classmethod
    def set_threshold_profile_100_percent(
            cls,
            subscription_code,
            maximum_rate="1.0",
            is_prepaid=False,
    ):
        """
        :param is_prepaid:
        :param maximum_rate: maximum_ rate of a branch
        :param subscription_code:
        :return: bool True if succeed
        """
        notif_name = CGRatesConventions.notif_100_percent_postpaid()
        balance_id = CGRatesConventions.balance_postpaid()
        if is_prepaid:
            notif_name = CGRatesConventions.notif_100_percent_prepaid()
            balance_id = CGRatesConventions.balance_prepaid()
        account_name = CGRatesConventions.account_name(
            account_name=subscription_code,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
        )
        filter_ids = [
            f"*string:~*req.Account:{account_name}",
            "*string:~*req.EventType:BalanceUpdate",
            f"*string:~*req.BalanceID:{balance_id}",
            f"*lt:~*req.Units:{str(maximum_rate)}",
        ]
        threshold_id = CGRatesConventions.threshold(
            subscription_code,
            notif_name,
        )
        action_id = CGRatesConventions.call_url_action(
            notif_name,
        )

        return cls.set_threshold_profile(
            threshold_id=threshold_id,
            filter_ids=filter_ids,
            action_id=action_id,
        )

    @classmethod
    def remove_action_plan_balance_expiry(
            cls,
            subscription_code,
    ):
        """
        Only for prepaid balances
        :param subscription_code:
        :return: bool True if succeed
        """
        method = CGRatesMethods.remove_action_plan()
        body = [
            {
                "Id": CGRatesConventions.action_plans(subscription_code),
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.NotFound404:
            pass

        return True

    @classmethod
    def set_action_plan_balance_expiry(
            cls,
            subscription_code,
            expiry_time: datetime,
    ):
        """
        Only for prepaid balances
        :param expiry_time:
        :param subscription_code:
        :return: bool True if succeed
        """
        notif_name = CGRatesConventions.notif_expiry_prepaid()
        action_name = f"{subscription_code}_{notif_name}"
        action_id = cls.set_call_url_action_expiry(
            subscription_code,
            action_name,
        )

        method = CGRatesMethods.set_action_plan()
        body = [
            {
                "Id": CGRatesConventions.action_plans(subscription_code),
                "ReloadScheduler": True,
                "Overwrite": True,
                "ActionPlan": [
                    {
                        "Years": str(expiry_time.year),
                        "Months": str(expiry_time.month),
                        "MonthDays": str(expiry_time.day),
                        "Time": f"{str(expiry_time.hour).zfill(2)}:"
                                f"{str(expiry_time.minute).zfill(2)}:"
                                f"{str(expiry_time.second).zfill(2)}",
                        "ActionsId": action_id,
                        "Weight": BasicConfigurations.Priority.LOW,
                    }
                ],
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def get_cdrs_count(
            cls,
            subscription_codes=None,
            setup_time_start=None,
            setup_time_end=None,
            created_at_start=None,
            created_at_end=None,
            destination_prefixes=None,
            not_destination_prefixes=None,
            order_by='SetupTime;desc',
    ):
        """
        :param order_by: in this format {fieldName;desc/asc}
        :param subscription_codes: list of strings (subscription codes)
        :param setup_time_start: timestamp without milliseconds
        :param setup_time_end: timestamp without milliseconds
        :param created_at_start: timestamp without milliseconds
        :param created_at_end: timestamp without milliseconds
        :param created_at_end: timestamp without milliseconds
        :param destination_prefixes: list of strings
        :param not_destination_prefixes: list of strings
        :return: list of rated cdrs
        """
        if destination_prefixes is None:
            destination_prefixes = []
        if not_destination_prefixes is None:
            not_destination_prefixes = []
        subscription_codes_convention = []
        if subscription_codes is not None:
            for code in subscription_codes:
                subscription_codes_convention.append(
                    CGRatesConventions.account_name(
                        account_name=code,
                        account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][
                            0],
                    ),
                )

        method = CGRatesMethods.get_cdrs_count()
        body = [
            {
                "RunIDs": [
                    CGRatesConventions.default_charger()
                ],
                "Tenants": [
                    CGRatesConventions.default_tenant()
                ],
                "Accounts": subscription_codes_convention,
                "SetupTimeStart": setup_time_start,
                "SetupTimeEnd": setup_time_end,
                "CreatedAtStart": created_at_start,
                "CreatedAtEnd": created_at_end,
                "DestinationPrefixes": destination_prefixes,
                "NotDestinationPrefixes": not_destination_prefixes,
                "ExtraArgs": {
                    "MinCost": 0
                },
                "OrderBy": order_by,
            }
        ]
        try:
            cdrs_count = cls.__get_response(method, body)
        except api_exceptions.NotFound404:
            cdrs_count = 0

        return cdrs_count

    @classmethod
    def get_cdrs(
            cls,
            subscription_codes=None,
            setup_time_start=None,
            setup_time_end=None,
            created_at_start=None,
            created_at_end=None,
            destination_prefixes=None,
            not_destination_prefixes=None,
            subjects=None,
            not_subjects=None,
            extra_fields=None,
            not_extra_fields=None,
            order_by='SetupTime;desc',
            limit=None,
            offset=None,
    ):
        """
        :param subjects:
        :param not_subjects:
        :param not_extra_fields:
        :param extra_fields:
        :param order_by: in this format {fieldName;desc/asc}
        :param limit: limit for pagination
        :param offset: offset for pagination
        :param subscription_codes: list of strings (subscription codes)
        :param setup_time_start: timestamp without milliseconds
        :param setup_time_end: timestamp without milliseconds
        :param created_at_start: timestamp without milliseconds
        :param created_at_end: timestamp without milliseconds
        :param created_at_end: timestamp without milliseconds
        :param destination_prefixes: list of strings
        :param not_destination_prefixes: list of strings
        :return: list of rated cdrs
        """
        if subjects is None:
            subjects = []

        if not_subjects is None:
            not_subjects = []

        if destination_prefixes is None:
            destination_prefixes = []

        if not_destination_prefixes is None:
            not_destination_prefixes = []

        if extra_fields is None:
            extra_fields = {}

        if not_extra_fields is None:
            not_extra_fields = {}

        subscription_codes_convention = []
        if subscription_codes is not None:
            for code in subscription_codes:
                subscription_codes_convention.append(
                    CGRatesConventions.account_name(
                        account_name=code,
                        account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][
                            0],
                    ),
                )

        method = CGRatesMethods.get_cdrs()
        body = [
            {
                "RunIDs": [
                    CGRatesConventions.default_charger()
                ],
                "Tenants": [
                    CGRatesConventions.default_tenant()
                ],
                "Accounts": subscription_codes_convention,
                "SetupTimeStart": setup_time_start,
                "SetupTimeEnd": setup_time_end,
                "CreatedAtStart": created_at_start,
                "CreatedAtEnd": created_at_end,
                "DestinationPrefixes": destination_prefixes,
                "NotDestinationPrefixes": not_destination_prefixes,
                "Subjects": subjects,
                "NotSubjects": not_subjects,
                "ExtraFields": extra_fields,
                "NotExtraFields": not_extra_fields,
                "ExtraArgs": {
                    "MinCost": 0
                },
                "Limit": limit,
                "Offset": offset,
                "OrderBy": order_by,
            }
        ]
        try:
            cdrs = cls.__get_response(method, body, timeout=None)
        except api_exceptions.NotFound404:
            cdrs = []

        return cdrs

    @classmethod
    def set_account_availability(
            cls,
            subscription_code,
            new_condition,
    ):
        print('befor delete_subscription_related_cache')
        cls.delete_subscription_related_cache(subscription_code)

        method = CGRatesMethods.set_account()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                    account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
                ),
                "ExtraOptions": {
                    "Disabled": new_condition
                },
            }
        ]

        cls.__get_response(method, body)

        return new_condition

    @classmethod
    def remove_account(
            cls,
            subscription_code,
    ):
        method = CGRatesMethods.remove_account()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                    account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
                ),
            }
        ]

        cls.__get_response(method, body)
        cls.delete_subscription_related_cache(subscription_code)

        return True

    @classmethod
    def set_account(
            cls,
            account_name,
            is_active=True,
            allow_negative=False,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
    ):
        """
        Set (Add/Update) an account in CGRateS
        :param account_name: subscription_code or operator's name
        :param is_active:
        :param allow_negative: allow negative balances
        :param account_type: based on BasicConfigurations.Types.ACCOUNT_TYPE
        :return:
        """
        extra_options = {}
        if is_active is not None:
            extra_options.update(
                {
                    "Disabled": not is_active,
                }
            )
        if allow_negative is not None:
            extra_options.update(
                {
                    "AllowNegative": allow_negative,
                }
            )
        method = CGRatesMethods.set_account()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=account_name,
                    account_type=account_type,
                ),
                "ExtraOptions": extra_options,
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def set_balance_postpaid(
            cls,
            subscription_code,
            value,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
            disabled=False,
    ):
        balance_dict = {
            "ID": CGRatesConventions.balance_postpaid(),
            "Disabled": disabled,
        }
        if value is not None:
            balance_dict.update(
                {
                    "Value": int(value)
                }
            )

        method = CGRatesMethods.set_balance()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                    account_type=account_type,
                ),
                "BalanceType": CGRatesConventions.balance_monetary(),
                "Balance": balance_dict,
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def set_balance_prepaid(
            cls,
            subscription_code,
            value,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
            disabled=False,
    ):
        balance_dict = {
            "ID": CGRatesConventions.balance_prepaid(),
            "Disabled": disabled,
        }
        if value is not None:
            balance_dict.update(
                {
                    "Value": int(value)
                }
            )

        method = CGRatesMethods.set_balance()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                    account_type=account_type,
                ),
                "BalanceType": CGRatesConventions.balance_monetary(),
                "Balance": balance_dict,
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def set_balance(
            cls,
            subscription_code,
            value,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
            is_prepaid=False,
            expiry_date=None,
    ):
        """
        Sets two new balances for a subscription
        :param expiry_date:
        :param subscription_code:
        :param value:
        :param account_type:
        :param is_prepaid:
        :return:
        """
        if is_prepaid:
            # *prepaid is enabled and *postpaid is disabled
            cls.set_balance_postpaid(
                subscription_code,
                None,
                account_type,
                disabled=True,
            )
            cls.set_balance_prepaid(
                subscription_code,
                value,
                account_type,
                disabled=False,
            )
            cls.set_action_plan_balance_expiry(
                subscription_code,
                expiry_date,
            )
        else:
            # *prepaid is disabled and *postpaid is disabled enabled
            cls.set_balance_postpaid(
                subscription_code,
                value,
                account_type,
                disabled=False,
            )
            cls.set_balance_prepaid(
                subscription_code,
                None,
                account_type,
                disabled=True,
            )

        return True

    @classmethod
    def debit_balance(
            cls,
            subscription_code,
            value,
            is_prepaid=False,
    ):
        balance_id = CGRatesConventions.balance_postpaid()
        if is_prepaid:
            balance_id = CGRatesConventions.balance_prepaid()

        cls.delete_subscription_related_cache(subscription_code)
        method = CGRatesMethods.debit_balance()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Account": CGRatesConventions.account_name(
                    account_name=subscription_code,
                    account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
                ),
                "BalanceType": CGRatesConventions.balance_monetary(),
                "Balance": {
                    "ID": balance_id,
                    "Value": int(float(value)),
                },
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def set_attribute_profile_account(
            cls,
            subscription_code,
            number,
            subscription_type,
            branch_code,
            emergency_branch=
            FinanceConfigurations.Destination.EMERGENCY_NAME[0],
            emergency_numbers=None,
    ):
        """
        This method converts the number of a subscription to a custom account
        :param emergency_branch:
        :param emergency_numbers:
        :param subscription_type: from Subscription model
        :param subscription_code: from Subscription model
        :param number: from Subscription model
        :param branch_code: from Branch model
        :return: mixed (boolean or exception)
        """
        if emergency_numbers is None:
            emergency_numbers = []
        method = CGRatesMethods.set_attribute_profile()
        direction_field = CGRatesConventions.extra_field_direction()
        account_type_filed = CGRatesConventions.extra_field_balance_type()
        filter_emergency = "*string:~*req.Destination:"
        if not emergency_numbers:
            filter_emergency = ""
        for em_number in emergency_numbers:
            filter_emergency += f"{em_number};"
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": CGRatesConventions.attribute_profile(
                    attribute_name=subscription_code,
                    attribute_type=BasicConfigurations.Types.ATTRIBUTE_TYPE[0][
                        0],
                ),
                "Contexts":
                    [
                        "*any"
                    ],
                "FilterIDs":
                    [
                        f"*string:~*req.Account:{number}"
                    ],
                "Attributes":
                    [
                        {
                            "Path": "*req.Account",
                            "Type": "*constant",
                            "Value": CGRatesConventions.account_name(
                                account_name=subscription_code,
                                account_type=
                                BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
                            ),
                        },
                        {
                            "Path": "*req.Subject",
                            "Type": "*constant",
                            "Value": number,
                        },
                        {
                            "Path": "*req.Category",
                            "Type": "*constant",
                            "Value": CGRatesConventions.branch_name(
                                branch_code
                            ),
                        },
                        {
                            "FilterIDs": [filter_emergency],
                            "Path": "*req.Category",
                            "Type": "*constant",
                            "Value": CGRatesConventions.branch_name(
                                emergency_branch
                            ),
                        },
                        {
                            "Path": f"*req.{direction_field}",
                            "Type": "*constant",
                            "Value":
                                CGRatesConventions.direction_outbound(),
                        },
                        {
                            "Path": f"*req.{account_type_filed}",
                            "Type": "*constant",
                            "Value": subscription_type,
                        }
                    ],
                "Weight": BasicConfigurations.Priority.CRITICAL,
                "ActivationInterval": None,
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def set_attribute_profile_inbound(
            cls,
            operator_code,
            prefixes,
            priority=BasicConfigurations.Priority.MEDIUM,
    ):
        """
        This method converts the category of an account to a custom branch
        :param priority:
        :param operator_code:
        :param prefixes:
        :return: mixed (boolean or exception)
        """
        account_name = CGRatesConventions.account_name(
            account_name=operator_code,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[1][0],
        )
        branch_name = CGRatesConventions.branch_name(
            FinanceConfigurations.Branch.DEFAULT_BRANCH_CODE[0],
        )
        filter_string = "*prefix:~*req.Account:"
        for prefix in prefixes:
            filter_string += f"{prefix};"
        filter_string = filter_string[:-1]
        direction_field = CGRatesConventions.extra_field_direction()
        operator_field = CGRatesConventions.extra_field_operator()
        method = CGRatesMethods.set_attribute_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": CGRatesConventions.attribute_profile(
                    attribute_name=operator_code,
                    attribute_type=BasicConfigurations.Types.ATTRIBUTE_TYPE[1][
                        0],
                ),
                "Contexts":
                    [
                        "*any"
                    ],
                "FilterIDs": [filter_string],
                "Attributes":
                    [
                        {
                            "Path": f"*req.{direction_field}",
                            "Type": "*constant",
                            "Value": CGRatesConventions.direction_inbound(),
                        },
                        {
                            "Path": f"*req.{operator_field}",
                            "Type": "*constant",
                            "Value": operator_code,
                        },
                        {
                            "Path": "*req.Subject",
                            "Type": "*variable",
                            "Value": "~*req.Account",
                        },
                        {
                            "Path": "*req.Account",
                            "Type": "*constant",
                            "Value": account_name,
                        },
                        {
                            "Path": "*req.Category",
                            "Type": "*constant",
                            "Value": branch_name,
                        },
                    ],
                "Weight": priority,
                "ActivationInterval": None,
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_attribute_profile(
            cls,
            attribute_name,
            attribute_type=BasicConfigurations.Types.ATTRIBUTE_TYPE[0][0],
    ):
        """
        Removes an attribute profile based on attribute type
        :param attribute_name: from Subscription model
        :param attribute_type: equal to CGRatesConventions.attribute_profile
        :return: mixed (boolean or exception)
        """
        method = CGRatesMethods.remove_attribute_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": CGRatesConventions.attribute_profile(
                    attribute_name,
                    attribute_type,
                ),
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.NotFound404:
            pass

        return True

    @classmethod
    def account_object(cls, body):
        account_object = AccountSerializer(
            data=body
        )

        if not account_object.is_valid():
            raise api_exceptions.ValidationError400(
                detail=account_object.errors,
            )

        return account_object.data

    @classmethod
    def cdrs_object(cls, cdrs):
        cdrs_serializer = CDRSerializer(data=cdrs, many=True)

        if not cdrs_serializer.is_valid():
            raise api_exceptions.ValidationError400({
                'non_fields': _('CDRs from cgrates are invalid')
            })

        return cdrs_serializer.data

    @classmethod
    def cdrs_minimal_object(cls, cdrs):
        cdrs_serializer = CDRMinimalSerializer(data=cdrs, many=True)

        if not cdrs_serializer.is_valid():
            raise api_exceptions.ValidationError400({
                'non_fields': _('CDRs from cgrates are invalid')
            })

        return cdrs_serializer.data

    @classmethod
    def balances_object(cls, account_details):
        if account_details['BalanceMap'] is None or \
                account_details['BalanceMap']['*monetary'] is None:
            raise api_exceptions.ValidationError400(
                _("The account has no balance defined")
            )

        balances_object = BalanceSerializer(
            data=account_details['BalanceMap']['*monetary'],
            many=True,
        )

        if not balances_object.is_valid():
            raise api_exceptions.ValidationError400(
                balances_object.errors
            )

        return balances_object.data

    @classmethod
    def get_toggle_subscription(cls, data):
        toggle_body = ToggleSubscriptionSerializer(data=data)

        if not toggle_body.is_valid():
            raise api_exceptions.ValidationError400(
                detail=toggle_body.errors,
            )

        return toggle_body.data

    @classmethod
    def remove_actions(
            cls,
            action_ids,
    ):
        """
        Get actions with limit and offset using v2 api
        :param action_ids: list of action ids
        :return:
        """
        method = CGRatesMethods.remove_actions_v2()
        body = [
            {
                "ActionIds": action_ids,
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.NotFound404:
            pass

        return True

    @classmethod
    def get_actions(
            cls,
            action_ids,
            limit,
            offset,
    ):
        """
        Get actions with limit and offset using v2 api
        :param action_ids:
        :param limit:
        :param offset:
        :return:
        """
        method = CGRatesMethods.get_actions_v2()
        body = [
            {
                "ActionIds": action_ids,
                "Limit": limit,
                "Offset": offset
            }
        ]

        try:
            actions_objects = cls.__get_response(method, body)
        except api_exceptions.APIException:
            actions_objects = []

        if actions_objects:
            if isinstance(actions_objects, dict):
                actions_objects = list(actions_objects.values())
            actions_objects_list = []
            for action_object in actions_objects:
                actions_objects_list.append(action_object[0])

            actions_serializer = ActionsV2Serializer(
                data=actions_objects_list,
                many=True,
            )

            if not actions_serializer.is_valid():
                raise api_exceptions.ValidationError400(
                    actions_serializer.errors
                )
            actions_objects = actions_serializer.data

        return actions_objects

    @classmethod
    def get_attributes(cls, limit, offset):
        method = CGRatesMethods.get_attribute_profile_ids()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        attributes_objects = cls.__get_response(method, body)

        return attributes_objects

    @classmethod
    def get_destinations(cls, destinations):
        method = CGRatesMethods.get_destinations()
        body = [
            {
                "DestinationIDs": destinations,
            }
        ]
        destinations_objects = cls.__get_response(method, body)

        destinations_serializer = DestinationSerializer(
            data=destinations_objects,
            many=True,
        )

        if destinations_serializer.is_valid(raise_exception=True):
            destinations_objects = destinations_serializer.data

        return destinations_objects

    @classmethod
    def get_attribute(cls, attribute):
        method = CGRatesMethods.get_attribute_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": attribute
            }
        ]
        attribute_object = cls.__get_response(method, body)
        attribute_serializer = AttributeProfileSerializer(
            data=attribute_object,
        )

        if attribute_serializer.is_valid(raise_exception=True):
            attribute_object = attribute_serializer.data

        return attribute_object

    @classmethod
    def get_thresholds(
            cls,
            limit,
            offset
    ):
        method = CGRatesMethods.get_threshold_profile_ids()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        thresholds_objects = cls.__get_response(method, body)

        return thresholds_objects

    @classmethod
    def get_threshold(cls, threshold):
        method = CGRatesMethods.get_threshold_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": threshold
            }
        ]
        threshold_object = cls.__get_response(method, body)
        threshold_serializer = ThresholdProfileSerializer(
            data=threshold_object,
        )

        if threshold_serializer.is_valid(raise_exception=True):
            threshold_object = threshold_serializer.data

        return threshold_object

    @classmethod
    def get_filter(cls, filter_name):
        method = CGRatesMethods.get_filter()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": filter_name
            }
        ]
        filter_object = cls.__get_response(method, body)
        filter_serializer = FilterSerializer(
            data=filter_object,
        )

        if filter_serializer.is_valid(raise_exception=True):
            filter_object = filter_serializer.data

        return filter_object

    @classmethod
    def get_filters(
            cls,
            limit,
            offset
    ):
        method = CGRatesMethods.get_filter_ids()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        filters_objects = cls.__get_response(method, body)

        return filters_objects

    @classmethod
    def get_suppliers(cls, limit, offset):
        method = CGRatesMethods.get_supplier_profile_ids()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        suppliers_objects = cls.__get_response(method, body)

        return suppliers_objects

    @classmethod
    def get_supplier(cls, supplier):
        method = CGRatesMethods.get_supplier_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": supplier
            }
        ]
        supplier_object = cls.__get_response(method, body)
        supplier_serializer = SupplierProfileSerializer(
            data=supplier_object,
        )

        if supplier_serializer.is_valid(raise_exception=True):
            supplier_object = supplier_serializer.data

        return supplier_object

    @classmethod
    def get_charger_profile(cls, charger):
        method = CGRatesMethods.get_charger_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": charger
            }
        ]
        charger_object = cls.__get_response(method, body)
        charger_serializer = ChargerProfileSerializer(
            data=charger_object,
        )

        if charger_serializer.is_valid(raise_exception=True):
            charger_object = charger_serializer.data

        return charger_object

    @classmethod
    def set_charger_profile(cls):
        method = CGRatesMethods.set_charger_profile()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": CGRatesConventions.default_charger_identifier(),
                "FilterIDs": [],
                "ActivationInterval": None,
                "RunID": CGRatesConventions.default_charger(),
                "AttributeIDs": [
                    "*none"
                ],
                "Weight": BasicConfigurations.Priority.NORMAL,
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def get_chargers(cls, limit, offset):
        method = CGRatesMethods.get_charger_profile_ids()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        chargers_objects = cls.__get_response(method, body)

        return chargers_objects

    @classmethod
    def get_rate(cls, rate):
        method = CGRatesMethods.get_rate()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": rate
            }
        ]
        rate_object = cls.__get_response(method, body)
        rate_serializer = RateSerializer(
            data=rate_object,
        )

        if rate_serializer.is_valid(raise_exception=True):
            rate_object = rate_serializer.data

        return rate_object

    @classmethod
    def get_rates(cls, limit, offset):
        method = CGRatesMethods.get_rate_ids()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        rates_objects = cls.__get_response(method, body)

        return rates_objects

    @classmethod
    def get_destination_rate(cls, destination_rate):
        method = CGRatesMethods.get_destination_rate()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": destination_rate
            }
        ]
        destination_rate_object = cls.__get_response(method, body)
        destination_rate_serializer = DestinationRateSerializer(
            data=destination_rate_object,
        )

        if destination_rate_serializer.is_valid(raise_exception=True):
            destination_rate_object = destination_rate_serializer.data

        return destination_rate_object

    @classmethod
    def get_destination_rates(cls, limit, offset):
        method = CGRatesMethods.get_destination_rate_ids()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        destination_rate_objects = cls.__get_response(method, body)

        return destination_rate_objects

    @classmethod
    def get_timing(cls, timing):
        method = CGRatesMethods.get_timing()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": timing
            }
        ]
        timing_object = cls.__get_response(method, body)
        timing_object_serializer = TimingSerializer(
            data=timing_object,
        )

        if timing_object_serializer.is_valid(raise_exception=True):
            timing_object = timing_object_serializer.data

        return timing_object

    @classmethod
    def get_timings(cls, limit, offset):
        method = CGRatesMethods.get_timing_ids()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        timings_objects = cls.__get_response(method, body)

        return timings_objects

    @classmethod
    def get_rating_plans(cls, limit, offset):
        method = CGRatesMethods.get_rating_plan_ids()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        rating_plan_objects = cls.__get_response(method, body)

        return rating_plan_objects

    @classmethod
    def get_rating_plan(cls, rating_plan):
        method = CGRatesMethods.get_rating_plan()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": rating_plan
            }
        ]
        rating_plan_object = cls.__get_response(method, body)
        rating_plan_serializer = RatingPlanSerializer(
            data=rating_plan_object,
        )

        if rating_plan_serializer.is_valid(raise_exception=True):
            rating_plan_object = rating_plan_serializer.data

        return rating_plan_object

    @classmethod
    def get_rating_profiles(cls, limit, offset):
        method = CGRatesMethods.get_rating_profile_ids()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "Limit": limit,
                "Offset": offset
            }
        ]
        rating_profiles_objects = cls.__get_response(method, body)

        return rating_profiles_objects

    @classmethod
    def get_rating_profile(cls, rating_profile):
        method = CGRatesMethods.get_rating_profile()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "LoadId": rating_profile
            }
        ]

        rating_profile_object = cls.__get_response(method, body)
        rating_profile_serializer = RatingProfileSerializer(
            data=rating_profile_object,
            many=True,
        )

        if rating_profile_serializer.is_valid(raise_exception=True):
            rating_profile_object = rating_profile_serializer.data

        return rating_profile_object

    @classmethod
    def load_tariff_plan(cls):
        method = CGRatesMethods.load_tariff_plan_from_database()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "DryRun": False,
                "Validate": True,
            }
        ]

        return cls.__get_response(method, body)

    @classmethod
    def set_destination(cls, code_name, name, prefixes):
        """
        :param code_name:
        :param name:
        :param prefixes: list of prefixes
        :return:
        """
        method = CGRatesMethods.set_destination()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": CGRatesConventions.destination(
                    code_name,
                    name,
                ),
                "Prefixes": prefixes,
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_destination(
            cls,
            code_name,
            name,
    ):
        """
        :param code_name:
        :param name:
        :return:
        """
        destination_id = CGRatesConventions.destination(
            code_name,
            name,
        )
        method = CGRatesMethods.remove_tp_destination()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": destination_id,
            }
        ]
        try:
            if cls.__get_response(method, body):
                method = CGRatesMethods.remove_destination()
                body = [
                    {
                        "DestinationIDs": [destination_id],
                    }
                ]
                try:
                    cls.__get_response(method, body)
                except api_exceptions.NotFound404:
                    pass

                return True
        except api_exceptions.NotFound404:
            return True

        return False

    @classmethod
    def remove_rate(cls, rate):
        method = CGRatesMethods.remove_tp_rate()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": rate
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_rate(cls, body):
        """
        :param body:
        :return:
        """
        method = CGRatesMethods.set_tp_rate()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                **body
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_destination_rate(cls, destination_rate):
        """
        :param destination_rate:
        :return:
        """
        method = CGRatesMethods.remove_tp_destination_rate()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": destination_rate
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_destination_rate(cls, body):
        """
        :param body:
        :return:
        """
        method = CGRatesMethods.set_tp_destination_rate()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                **body
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def set_timings(cls, body):
        """
        :param body:
        :return:
        """
        method = CGRatesMethods.set_tp_timing()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                **body
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_timing(cls, timing):
        """
        :param timing:
        :return:
        """
        method = CGRatesMethods.remove_tp_timing()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": timing
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_rating_plan(cls, data):
        """
        :param data:
        :return:
        """
        method = CGRatesMethods.set_rating_plan()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                **data
            }
        ]
        cls.__get_response(method, body)
        cls.set_supplier_profile()

        return True

    @classmethod
    def remove_rating_plan(cls, rating_plan):
        """
        :param rating_plan:
        :return:
        """
        method = CGRatesMethods.remove_rating_plan()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "ID": rating_plan
            }
        ]
        cls.__get_response(method, body)
        cls.set_supplier_profile()

        return True

    @classmethod
    def set_rating_profile(cls, data):
        """
        :param data:
        :return:
        """
        method = CGRatesMethods.set_rating_profile()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "LoadId": CGRatesConventions.default_load_identifier(),
                "Tenant": CGRatesConventions.default_tenant(),
                **data
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def remove_rating_profile(cls, rating_profile, category, subject):
        rating_profile_id = \
            CGRatesConventions.get_rating_profile_id_from_category_and_subject(
                category,
                subject,
                rating_profile,
            )
        method = CGRatesMethods.remove_rating_profile()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "RatingProfileId": rating_profile_id,
            }
        ]
        cls.__get_response(method, body)

        return True

    @classmethod
    def set_supplier_profile(
            cls,
    ):
        """
        This method sets the default supplier profile with all rating plans
        :return: mixed (boolean or exception)
        """
        rating_plans = cls.get_rating_plans(None, None)
        method = CGRatesMethods.set_tp_supplier_profile()
        body = [
            {
                "TPid": CGRatesConventions.default_tariff_plans(),
                "Tenant": CGRatesConventions.default_tenant(),
                "ID": CGRatesConventions.default_supplier(),
                "FilterIDs": None,
                "ActivationInterval": None,
                "Sorting": "*weight",
                "SortingParameters": [
                    ""
                ],
                "Suppliers": [
                    {
                        "ID": CGRatesConventions.default_supplier(),
                        "FilterIDs": None,
                        "AccountIDs": None,
                        "RatingPlanIDs": rating_plans,
                        "ResourceIDs": None,
                        "StatIDs": None,
                        "Weight": BasicConfigurations.Priority.CRITICAL,
                        "Blocker": None,
                        "SupplierParameters": ""
                    }
                ],
                "Weight": BasicConfigurations.Priority.CRITICAL,
            }
        ]

        cls.__get_response(method, body)

        return True

    @classmethod
    def get_branch_minimum_rate(cls, branch_code):
        """
        This method is heavily related to CGRateSConventions
        :param branch_code:
        :return:
        """
        minimum_rate = Cache.get(
            key=Cache.KEY_CONVENTIONS['minimum_rate'],
            values={
                'branch_code': branch_code,
            },
        )

        if not minimum_rate:
            try:
                destination_rates = cls.get_destination_rate(
                    destination_rate=CGRatesConventions.destination_rate(
                        destination_rate_name=branch_code,
                    )
                )
                rates_fee = []
                for destination_rate in destination_rates["destination_rates"]:
                    rates = cls.get_rate(
                        rate=destination_rate["rate_id"],
                    )
                    for rate_slot in rates['rate_slots']:
                        rates_fee.append(
                            float(rate_slot['rate']) if float(
                                rate_slot['connect_fee']) == float(
                                0) else float(rate_slot['connect_fee'])
                        )
                rates_fee = list(
                    filter(
                        lambda num: float(num) != float(0),
                        rates_fee,
                    )
                )
                minimum_rate = min(rates_fee)
            except api_exceptions.APIException:
                minimum_rate = 1

            if minimum_rate < 1:
                minimum_rate = 1

            Cache.set(
                key=Cache.KEY_CONVENTIONS['minimum_rate'],
                values={
                    'branch_code': branch_code,
                },
                store_value=minimum_rate,
            )

        return str(minimum_rate)

    @classmethod
    def get_branch_maximum_rate(cls, branch_code):
        """
        This method is related to CGRateSConventions
        :param branch_code:
        :return:
        """
        maximum_rate = Cache.get(
            key=Cache.KEY_CONVENTIONS['maximum_rate'],
            values={
                'branch_code': branch_code,
            },
        )

        if not maximum_rate:
            rates_fee = []
            try:
                rating_plans = cls.get_rating_plan(
                    rating_plan=CGRatesConventions.rating_plan(
                        rating_plan_name=branch_code,
                    )
                )
            except api_exceptions.APIException:
                rating_plans = None
            if rating_plans:
                for rating_plan in rating_plans['rating_plan_bindings']:
                    if rating_plan['destination_rates_id'] != \
                            CGRatesConventions.destination_rate(
                                # @TODO: Not a good way though, think of a
                                #  way to make this name dynamic
                                "International",
                            ):
                        try:
                            destination_rates = \
                                cls.get_destination_rate(
                                    rating_plan['destination_rates_id'],
                                )
                        except api_exceptions.APIException:
                            destination_rates = None
                        if destination_rates:
                            fee = []
                            for dr in destination_rates["destination_rates"]:
                                rates = cls.get_rate(
                                    rate=dr["rate_id"],
                                )
                                for rate_slot in rates['rate_slots']:
                                    fee.append(
                                        float(rate_slot['rate']) if float(
                                            rate_slot['connect_fee']) == float(
                                            0) else float(
                                            rate_slot['connect_fee'])
                                    )
                            fee = list(
                                filter(
                                    lambda num: float(num) != float(0),
                                    fee,
                                )
                            )
                            rates_fee.extend(fee)

            if len(rates_fee):
                maximum_rate = max(rates_fee)
                if maximum_rate < 1:
                    maximum_rate = 1
            else:
                maximum_rate = 1

            Cache.set(
                key=Cache.KEY_CONVENTIONS['maximum_rate'],
                values={
                    'branch_code': branch_code,
                },
                store_value=maximum_rate,
            )

        return str(maximum_rate)

    @classmethod
    def disconnect_sessions(cls, subscription_code, setup_time):
        """
        Force disconnect a sessions
        :param subscription_code:
        :param setup_time: datetime
        :return:
        """
        filters = []
        if subscription_code:
            account = CGRatesConventions.account_name(subscription_code)
            filters.append(f"*string:~*req.Account:{account}")
        if setup_time:
            setup_time = str(setup_time.timestamp()).split('.')[0]
            filters.append(f"*lte:~*req.SetupTime:{setup_time}")
        method = CGRatesMethods.force_disconnect()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": None,
                "Filters": filters,
            }
        ]
        try:
            cls.__get_response(method, body)
        except api_exceptions.APIException:
            pass

        return True

    @classmethod
    def get_active_sessions(
            cls,
            subscription_code,
    ):
        """
        Get all active sessions of an account
        :return: bool True if succeed
        """
        flt = []
        if subscription_code:
            account = CGRatesConventions.account_name(subscription_code)
            flt = [f"*string:~*req.Account:{account}"]
        method = CGRatesMethods.get_active_sessions()
        body = [
            {
                "Tenant": CGRatesConventions.default_tenant(),
                "Limit": None,
                "Filters": flt
            }
        ]
        try:
            sessions = cls.__get_response(method, body)
        except api_exceptions.APIException:
            return []

        sessions = ActiveSessionsV1Serializer(
            data=sessions,
            many=True,
        )

        if not sessions.is_valid():
            return []

        return sessions.data
