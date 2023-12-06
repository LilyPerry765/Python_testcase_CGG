# --------------------------------------------------------------------------
# Override python's requests to handle outgoing request logging
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - requests.py
# Created at 2020-8-29,  16:2:23
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import requests

from cgg.core.tools import Tools


class Requests:
    @classmethod
    def get(cls, label, app_name, *args, **kwargs):
        response = requests.get(*args, **kwargs)
        kwargs['method'] = 'get'
        kwargs['label'] = label
        kwargs['app_name'] = app_name
        Tools.log_outgoing_requests(
            kwargs=kwargs,
            response=response,
            app_name=app_name,
            label=label,
        )

        return response

    @classmethod
    def put(cls, label, app_name, *args, **kwargs):
        response = requests.put(*args, **kwargs)
        kwargs['method'] = 'put'
        kwargs['label'] = label
        kwargs['app_name'] = app_name
        Tools.log_outgoing_requests(
            kwargs=kwargs,
            response=response,
            app_name=app_name,
            label=label,
        )

        return response

    @classmethod
    def patch(cls, label, app_name, *args, **kwargs):
        response = requests.patch(*args, **kwargs)
        kwargs['method'] = 'patch'
        kwargs['label'] = label
        kwargs['app_name'] = app_name
        Tools.log_outgoing_requests(
            kwargs=kwargs,
            response=response,
            app_name=app_name,
            label=label,
        )

        return response

    @classmethod
    def post(cls, label, app_name, *args, **kwargs):
        response = requests.post(*args, **kwargs)
        kwargs['method'] = 'post'
        kwargs['label'] = label
        kwargs['app_name'] = app_name
        Tools.log_outgoing_requests(
            kwargs=kwargs,
            response=response,
            app_name=app_name,
            label=label,
        )

        return response

    @classmethod
    def options(cls, label, app_name, *args, **kwargs):
        response = requests.options(*args, **kwargs)
        kwargs['method'] = 'options'
        kwargs['label'] = label
        kwargs['app_name'] = app_name
        Tools.log_outgoing_requests(
            kwargs=kwargs,
            response=response,
            app_name=app_name,
            label=label,
        )

        return response

    @classmethod
    def delete(cls, label, app_name, *args, **kwargs):
        response = requests.delete(*args, **kwargs)
        kwargs['method'] = 'delete'
        kwargs['label'] = label
        kwargs['app_name'] = app_name
        Tools.log_outgoing_requests(
            kwargs=kwargs,
            response=response,
            app_name=app_name,
            label=label,
        )

        return response
