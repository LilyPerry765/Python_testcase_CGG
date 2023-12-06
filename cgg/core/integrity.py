# --------------------------------------------------------------------------
# Integrity checker for objects of models.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - integrity.py
# Created at 2020-8-29,  15:59:31
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
from datetime import datetime
from decimal import Decimal
from hashlib import sha512

import uuid
from django.conf import settings
from django.db import models
from django.db.models import ForeignKey


def _convert_to_string(param):
    if isinstance(param, Decimal) or isinstance(param, float):
        return f"{param:.2f}"
    if isinstance(param, datetime):
        return str(param.timestamp())
    if isinstance(param, uuid.UUID):
        return str(param.hex)
    if not hasattr(param, '__dict__'):
        return param

    param = str(param)
    return param


def _is_fk(model, key):
    field_object = model._meta.get_field(key)
    if isinstance(field_object, ForeignKey):
        return True
    return False


class Integrity:
    @classmethod
    def check(cls, model_object: models.Model):
        try:
            model_object._meta.get_field('checksum')
        except models.FieldDoesNotExist:
            return False
        if model_object.checksum is None or model_object.checksum == "" or \
                model_object.checksum == cls.checksum(model_object):
            return True

        return False

    @classmethod
    def checksum(cls, model_object: models.Model):
        object_vars = vars(model_object)
        checksum_dict = {
            'secret': settings.SECRET_KEY,
            'model_name': model_object._meta.model_name,
        }

        for key in object_vars.keys():
            if key not in (
                    '_state',
                    'checksum',
                    'created_at',
                    'updated_at',
            ):
                if not _is_fk(model_object, key):
                    checksum_dict[key] = _convert_to_string(object_vars[key])

        checksum = sha512(
            str(checksum_dict).encode('utf-8')
        ).hexdigest()
        return checksum
