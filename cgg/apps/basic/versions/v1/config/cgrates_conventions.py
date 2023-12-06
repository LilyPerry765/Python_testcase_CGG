# --------------------------------------------------------------------------
# Conventions for names and type. Never use a new convention without this proxy
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - cgrates_conventions.py
# Created at 2020-8-29,  16:22:27
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.conf import settings

from cgg.apps.basic.versions.v1.config import BasicConfigurations
from cgg.core.tools import Tools


class CGRatesConventions:

    @classmethod
    def extra_field_balance_type(cls):
        return "BalanceType"

    @classmethod
    def extra_field_direction(cls):
        return "CallDirection"

    @classmethod
    def extra_field_operator(cls):
        return "OperatorName"

    @classmethod
    def direction_inbound(cls):
        return "inbound"

    @classmethod
    def direction_outbound(cls):
        return "outbound"

    @classmethod
    def extra_field_inbound(cls):
        return {
            cls.extra_field_direction(): cls.direction_inbound(),
        }

    @classmethod
    def extra_field_outbound(cls):
        return {
            cls.extra_field_direction(): cls.direction_outbound(),
        }

    @classmethod
    def extra_field(cls, name, value):
        return {
            name: value
        }

    @classmethod
    def default_tenant(cls):
        return settings.CGG['DEFAULT_TENANT']

    @classmethod
    def default_tariff_plans(cls):
        return 'TRP_DEFAULT'

    @classmethod
    def default_supplier(cls):
        return 'SPL_DEFAULT'

    @classmethod
    def destination(
            cls,
            code_name,
            name,
    ):
        code_name = Tools.snake_case_to_camelcase(code_name)
        name = Tools.snake_case_to_camelcase(name)

        return f'DST_{code_name}_{name}'

    @classmethod
    def reverse_destination(
            cls,
            destination_convention,
    ):
        parts = destination_convention.split('_')
        code_name = parts[1]
        name = parts[2]

        return code_name, name

    @classmethod
    def destination_rate(
            cls,
            destination_rate_name,
    ):
        destination_rate_name = Tools.snake_case_to_camelcase(
            destination_rate_name,
        )

        return f'DR_{destination_rate_name}'

    @classmethod
    def rating_plan(
            cls,
            rating_plan_name,
    ):
        rating_plan_name = Tools.snake_case_to_camelcase(
            rating_plan_name)

        return f'RP_{rating_plan_name}'

    @classmethod
    def timings(
            cls,
            timing_name,
    ):
        timing_name = Tools.snake_case_to_camelcase(timing_name)

        return f'TIM_{timing_name}'

    @classmethod
    def rate(
            cls,
            rate_name,
    ):
        rate_name = Tools.snake_case_to_camelcase(rate_name)

        return f'RT_{rate_name}'

    @classmethod
    def reverse_rate(
            cls,
            rate_convention,
    ):
        return rate_convention.replace('RT_', '')

    @classmethod
    def default_load_identifier(cls):
        return 'RPL_DEFAULT'

    @classmethod
    def default_charger_identifier(cls):
        return 'DEFAULT'

    @classmethod
    def default_charger(cls):
        return '*default'

    @classmethod
    def account_name(
            cls,
            account_name,
            account_type=BasicConfigurations.Types.ACCOUNT_TYPE[0][0],
    ):
        """
        Return account name based on conventions
        :param account_name:
        :param account_type: based on BasicConfigurations.Types.ACCOUNT_TYPE
        :return:
        """
        if account_type == BasicConfigurations.Types.ACCOUNT_TYPE[1][0]:
            return f'AN_op-{account_name}'

        return f'AN_{account_name}'

    @classmethod
    def revert_account_name(
            cls,
            original_name,
            with_tenant=True,
    ):
        default_tenant = cls.default_tenant()
        if with_tenant:
            original_name = original_name.replace(f'{default_tenant}:', '')

        return original_name.replace('AN_', '')

    @classmethod
    def account_name_no_tenant(
            cls,
            original_name,
    ):
        default_tenant = cls.default_tenant()

        return original_name.replace(f'{default_tenant}:', '')

    @classmethod
    def notif_80_percent_postpaid(cls):
        return 'NOTIF80PO'

    @classmethod
    def notif_100_percent_postpaid(cls):
        return 'NOTIF100PO'

    @classmethod
    def notif_expiry_prepaid(cls):
        return 'NOTIFEXPIRE'

    @classmethod
    def notif_80_percent_prepaid(cls):
        return 'NOTIF80PR'

    @classmethod
    def notif_100_percent_prepaid(cls):
        return 'NOTIF100PR'

    @classmethod
    def balance_postpaid(cls):
        return '*postpaid'

    @classmethod
    def balance_prepaid(cls):
        return '*prepaid'

    @classmethod
    def balance_monetary(cls):
        return '*monetary'

    @classmethod
    def topup_reset_action(cls, subscription_code, is_prepaid):
        if is_prepaid:
            return f'ACT_TOPUP_PRE_{subscription_code}'

        return f'ACT_TOPUP_POST_{subscription_code}'

    @classmethod
    def call_url_action(cls, name):
        return f'ACT_URL_{name}'

    @classmethod
    def call_url_action_name(cls):
        return '*http_post'

    @classmethod
    def filter(cls, subscription_code, name):
        return f'FLT_{subscription_code}_{name}'

    @classmethod
    def threshold(cls, subscription_code, name):
        return f'THD_{subscription_code}_{name}'

    @classmethod
    def action_plans(cls, subscription_code):
        return f'ACP_{subscription_code}'

    @classmethod
    def attribute_profile(
            cls,
            attribute_name,
            attribute_type=BasicConfigurations.Types.ATTRIBUTE_TYPE[0][0],
    ):
        """
        return convention for attribute profile based on type
        :param attribute_name:
        :param attribute_type: based on
        BasicConfigurations.Types.ATTRIBUTE_TYPE
        :return:
        """
        if attribute_type == BasicConfigurations.Types.ATTRIBUTE_TYPE[0][0]:
            return f'ATTR_AN_{attribute_name}'
        elif attribute_type == BasicConfigurations.Types.ATTRIBUTE_TYPE[1][0]:
            return f'ATTR_IN_{attribute_name}'
        return f'ATTR_{attribute_name}'

    @classmethod
    def branch_name(cls, branch_code):
        branch_code = Tools.snake_case_to_camelcase(branch_code)

        return f'BR_{branch_code}'

    @classmethod
    def get_rating_profile_id_from_category_and_subject(
            cls,
            category,
            subject,
            rating_profile=None,
    ):
        """
        Generate rating profile id with CGRateS Service conventions.
        This method must change if CGRateS Service updates affect this
        convention
        :param rating_profile:
        :param category:
        :param subject:
        :return: str
        """
        if rating_profile is None:
            rating_profile = cls.default_load_identifier()

        return f"{rating_profile}::" \
               f"{cls.default_tenant()}:" \
               f"{category}:" \
               f"{subject}"
