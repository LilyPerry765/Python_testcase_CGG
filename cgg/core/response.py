# --------------------------------------------------------------------------
# Responses based on conventions
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - response.py
# Created at 2020-8-29,  16:3:12
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import codecs
import csv
from collections import OrderedDict
from datetime import datetime

from django.http import StreamingHttpResponse
from rest_framework.response import Response as DRFResponse


class Response(DRFResponse):
    def __init__(
            self,
            request,
            data=None,
            redirect_to=None,
            status=200,
            error=None,
            hint=None,
            message=None,
            pagination=True):
        r = OrderedDict()

        if data and request.method == 'GET' and status == 200 and not \
                isinstance(
                    data, dict) and pagination:
            data, paginator = data

            if paginator:
                r.update([
                    ('count', paginator.count),
                    ('next', paginator.get_next_link()),
                    ('previous', paginator.get_previous_link()),
                ])

        # Check Type of 'error'.
        if isinstance(error, Exception):
            error = error.__str__()

        r.update([
            ("status", status),
            ("error", error),
            ("hint", hint),
            ("message", message),
            ("user_id", request.user.id),
            ("time", datetime.now().timestamp()),
            ("data", data),
        ])

        if redirect_to:
            r.update([
                ('redirect_to', redirect_to),
            ])

        super(Response, self).__init__(data=r, status=status)


def response(
        request,
        status=200,
        data=None,
        error=None,
        hint=None,
        message=None,
        redirect_to=None,
        pagination=True,
):
    return Response(
        request=request,
        status=status,
        data=data,
        error=error,
        hint=hint,
        message=message,
        redirect_to=redirect_to,
        pagination=pagination,
    )


class Echo(object):
    """
    Pseudo buffer
    """

    def write(self, value):
        return value


def csv_response(
        data,
        name,
):
    """
    :param name:
    :type name:
    :type data: list of serialized dicts
    :return:
    :rtype:
    """

    def stream(rows):
        yield Echo().write(codecs.BOM_UTF8)
        writer = csv.writer(Echo())
        yield writer.writerow(rows[0].keys())
        for row in rows:
            yield writer.writerow(row.values())

    response_csv = StreamingHttpResponse(
        stream(data), content_type='text/csv',
    )
    response_csv['Content-Disposition'] = f"attachment; filename={name}.csv"

    return response_csv
