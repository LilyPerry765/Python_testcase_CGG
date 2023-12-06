# --------------------------------------------------------------------------
# A generic paginator for django ORM. Use it before accessing the data to
# decrease fetch time.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - paginator.py
# Created at 2020-8-29,  16:0:36
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from rest_framework.pagination import LimitOffsetPagination


class Paginator(LimitOffsetPagination):
    def __init__(self, **kwargs):
        self.count = None
        self.limit = None
        self.offset = None
        self.request = None

    def paginate_queryset(self, queryset, request, view=None):
        self.count = queryset.count()
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)
        self.request = request
        if self.count > self.limit and self.template is not None:
            self.display_page_controls = True

        if self.count == 0 or self.offset > self.count:
            return []
        return list(queryset[self.offset:self.offset + self.limit])

    def paginate(self, request, queryset):
        paginator = Paginator()
        if 'bypass_pagination' in request.query_params:
            return queryset, None

        queryset = paginator.paginate_queryset(
            request=request,
            queryset=queryset,
        )

        return queryset, paginator
