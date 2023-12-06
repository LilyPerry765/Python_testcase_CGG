# --------------------------------------------------------------------------
# Caching layer for dynamic keys. This class uses sha256 to generate keys
# and django's core caching system to store data.
# Note: always use get_key method before other methods to get correct keys
# based on KEY_CONVENTIONS.
# (C) 2019 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - cache.py
# Created at 2019-12-29,  12:6:16
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from hashlib import sha256

from django.core.cache import cache

from cgg.core import api_exceptions


class Cache:
    KEY_CONVENTIONS = {
        "base_balance_postpaid": "base_balance_postpaid",
        "base_balance_prepaid": "base_balance_prepaid",
        "account_details": "account_details",
        "maximum_rate": "maximum_rate",
        "minimum_rate": "minimum_rate",
        "runtime_config": "runtime_config",
    }

    @classmethod
    def set(cls, key, values: dict, store_value, expiry_time=None):
        """
        Set new (key, value) an cache
        :param key:
        :param values:
        :param store_value:
        :param expiry_time: in seconds
        :return:
        """
        cache_key = cls._get_key(key, **values)
        cache.set(cache_key, store_value, expiry_time)

    @classmethod
    def get(cls, key, values: dict):
        cache_key = cls._get_key(key, **values)
        return cache.get(cache_key)

    @classmethod
    def delete(cls, key, values: dict):
        cache_key = cls._get_key(key, **values)
        print('cache_key -> '+cache_key)
        cache.delete(cache_key)

    @classmethod
    def _get_key(cls, caching_key, **kwargs):
        """
        Return sha256 hashed key to store in cache table
        :param caching_key: from KEY_CONVENTIONS
        :param kwargs: key value (dict)
        :return:
        """
        if caching_key not in cls.KEY_CONVENTIONS:
            raise api_exceptions.Conflict409(
                "Caching error, use standard keys"
            )

        kwargs = json.dumps(kwargs)
        cache_key = sha256(
            str(f"{caching_key}:{kwargs}").encode('utf-8')
        )

        return cache_key.hexdigest()
