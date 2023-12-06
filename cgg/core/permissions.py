# --------------------------------------------------------------------------
# Token based permissions to handle accessing to APIs from outside
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - permissions.py
# Created at 2020-8-29,  16:1:41
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.conf import settings
from rest_framework import permissions

TOKENS = settings.CGG['AUTH_TOKENS']


class TrunkBackendAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return TOKENS['TRUNK_IN'] == request.META.get(
            'HTTP_AUTHORIZATION',
        )


class DashboardAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return TOKENS['CGRATES_DASHBOARD'] == request.META.get(
            'HTTP_AUTHORIZATION',
        )
