import uuid

from django.db import models
from django.db.models import JSONField

choices_http_methods = (
    ('options', 'options'),
    ('get', 'get'),
    ('post', 'post'),
    ('put', 'put'),
    ('delete', 'delete'),
    ('patch', 'patch'),
)

choices_direction_types = (
    ('in', 'in'),
    ('out', 'out'),
)


class APIRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    direction = models.CharField(
        max_length=8,
        choices=choices_direction_types,
        null=False,
        blank=False,
        default=choices_direction_types[0][0]
    )
    app_name = models.CharField(max_length=128, null=False, blank=False)
    label = models.CharField(
        max_length=128,
        null=False,
        blank=False,
        db_index=True,
    )
    ip = models.CharField(max_length=128, null=True, blank=True)
    http_method = models.CharField(
        max_length=8,
        choices=choices_http_methods,
        null=False,
        blank=False,
        db_index=True,
    )
    uri = models.CharField(max_length=1024, null=False, blank=False)
    status_code = models.SmallIntegerField(null=False, blank=False)
    request = JSONField(null=True, blank=True)
    response = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)
