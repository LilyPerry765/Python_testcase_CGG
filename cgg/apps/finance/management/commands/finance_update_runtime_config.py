# --------------------------------------------------------------------------
# Update RuntimeConfigs with default values
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_update_runtime_config.py
# Created at 2020-9-27,  9:22:53
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------


from django.core.management.base import BaseCommand

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.models import RuntimeConfig
from cgg.apps.finance.versions.v1.config import FinanceConfigurations


class Command(BaseCommand):
    help = 'Notify trunk-backend about passed due dates'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[12][0])
    def handle(self, *args, **options):
        keys = [
            k[0] for k in FinanceConfigurations.RuntimeConfig.KEY_CHOICES
        ]
        configs = RuntimeConfig.objects.all()
        # Delete old keys
        to_delete = []

        for config in configs:
            if config.item_key not in keys:
                to_delete.append(config.id)

        if to_delete:
            RuntimeConfig.objects.filter(
                id__in=to_delete,
            ).delete()

        # Add new keys
        exiting_keys = list(
            RuntimeConfig.objects.all().values_list('item_key', flat=True)
        )

        for key in keys:
            if key not in exiting_keys:
                r = RuntimeConfig()
                r.item_key = key
                r.item_value = \
                    FinanceConfigurations.RuntimeConfig.DEFAULT_VALUES[key]
                r.save()
