# --------------------------------------------------------------------------
# RuntimeConfig service get and updates the key and values related to
# payment cool down, invoice due date, corporate prefixes and etc.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - runtime_config.py
# Created at 2020-8-29,  17:41:21
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from cgg.apps.finance.models import RuntimeConfig
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.apps.finance.versions.v1.serializers.runtime_config import (
    RuntimeConfigsSerializer,
)
from cgg.core.cache import Cache
from cgg.core.tools import Tools


class RuntimeConfigService:

    @classmethod
    def get(cls):
        """
        Return RuntimeConfig key and values
        :return:
        :rtype:
        """
        keys = FinanceConfigurations.RuntimeConfig.KEY_CHOICES
        runtime_configs = RuntimeConfig.objects.all()
        payment_cool_down, deallocation_due, discount_percent, \
        discount_value, issue_hour, due_date, black_list_in_days = (
            None, None, None, None, None, None, None
        )
        for runtime_config in runtime_configs:
            if runtime_config.item_key == keys[5][0]:
                discount_percent = float(runtime_config.item_value)
            if runtime_config.item_key == keys[4][0]:
                discount_value = float(runtime_config.item_value)
            if runtime_config.item_key == keys[0][0]:
                issue_hour = int(runtime_config.item_value)
            if runtime_config.item_key == keys[1][0]:
                due_date = int(runtime_config.item_value)
            if runtime_config.item_key == keys[6][0]:
                deallocation_due = int(runtime_config.item_value)
            if runtime_config.item_key == keys[8][0]:
                payment_cool_down = int(runtime_config.item_value)
            if runtime_config.item_key == keys[9][0]:
                black_list_in_days = int(runtime_config.item_value)

        runtime_serializer = RuntimeConfigsSerializer(
            data={
                "discount_percent": discount_percent,
                "discount_value": discount_value,
                "issue_hour": issue_hour,
                "due_date": due_date,
                "deallocation_due": deallocation_due,
                "payment_cool_down": payment_cool_down,
                "black_list_in_days": black_list_in_days,
            },
        )
        if runtime_serializer.is_valid(raise_exception=True):
            data = runtime_serializer.data

            return data

    @classmethod
    def update(cls, body):
        """
        Update RuntimeConfig values and return updated data
        :param body:
        :type body:
        :return:
        :rtype:
        """
        keys = FinanceConfigurations.RuntimeConfig.KEY_CHOICES
        body = Tools.get_dict_from_json(body)
        runtime_serializer = RuntimeConfigsSerializer(
            data=body,
        )
        if runtime_serializer.is_valid(raise_exception=True):
            data = runtime_serializer.data
            if 'issue_hour' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[0][0]
                ).update(
                    item_value=str(int(data['issue_hour']))
                )
                cls.remove_cache(keys[0][0])

            if 'due_date' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[1][0]
                ).update(
                    item_value=str(int(data['due_date']))
                )
                cls.remove_cache(keys[1][0])

            if 'discount_percent' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[5][0]
                ).update(
                    item_value=str(float(data['discount_percent']))
                )
                cls.remove_cache(keys[5][0])

            if 'discount_value' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[4][0]
                ).update(
                    item_value=str(float(data['discount_value']))
                )
                cls.remove_cache(keys[4][0])

            if 'deallocation_due' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[6][0]
                ).update(
                    item_value=str(int(data['deallocation_due']))
                )
                cls.remove_cache(keys[6][0])

            if 'payment_cool_down' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[8][0]
                ).update(
                    item_value=str(int(data['payment_cool_down']))
                )
                cls.remove_cache(keys[8][0])

            if 'black_list_in_days' in data:
                RuntimeConfig.objects.filter(
                    item_key=keys[9][0]
                ).update(
                    item_value=str(int(data['black_list_in_days']))
                )
                cls.remove_cache(keys[9][0])

        return cls.get()

    @classmethod
    def get_value(cls, key):
        value = Cache.get(
            key=Cache.KEY_CONVENTIONS['runtime_config'],
            values={
                'key': key,
            },
        )
        if value is None:
            try:
                rc = RuntimeConfig.objects.get(
                    item_key=key
                )
                value = rc.item_value
                Cache.set(
                    key=Cache.KEY_CONVENTIONS['runtime_config'],
                    values={
                        'key': key,
                    },
                    store_value=value,
                )
            except RuntimeConfig.DoesNotExist:
                value = cls.get_default(key)

        return value

    @classmethod
    def remove_cache(cls, key):
        Cache.delete(
            key=Cache.KEY_CONVENTIONS['runtime_config'],
            values={
                'key': key,
            },
        )

    @classmethod
    def get_default(cls, key):
        return FinanceConfigurations.RuntimeConfig.DEFAULT_VALUES[key]
