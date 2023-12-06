import json

from django.contrib import admin

from cgg.apps.api_request.models import APIRequest


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    search_fields = ['app_name', 'label', 'ip', 'uri', ]
    list_display = (
        'label',
        'uri',
        'http_method',
        'direction',
        'status_code',
        'ip',
        'app_name',
        'created_at',
    )
    list_filter = ('direction', 'status_code', 'http_method',)
    ordering = ('-created_at',)
    list_per_page = 20
    fieldsets = (
        ('Base Information', {
            'fields': (
                'id',
                'app_name',
                'label',
                'uri',

            ),
        }),
        ('Request & Response', {
            'fields': (
                'ip',
                'http_method',
                'direction',
                'status_code',
                'request_formatted',
                'response_formatted',
            ),
        }),
        ('Dates', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def response_formatted(self, obj):
        return json.dumps(
            obj.response,
            ensure_ascii=False,
        )

    response_formatted.short_description = 'Response'

    def request_formatted(self, obj):
        return json.dumps(
            obj.request,
            ensure_ascii=False,
        )

    request_formatted.short_description = 'Request'
