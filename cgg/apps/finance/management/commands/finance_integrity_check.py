# --------------------------------------------------------------------------
# Randomly checks for any integrity errors in object of models.
# An anomaly in objects is related to changes made to objects outside of the
# CGG's logic, for example directly into the database.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - finance_integrity_check.py
# Created at 2020-8-29,  16:40:45
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import logging
import random

from django.apps import apps
from django.core.management.base import BaseCommand

from cgg.apps.finance.decorators import log_command
from cgg.apps.finance.versions.v1.config import FinanceConfigurations
from cgg.core.integrity import Integrity

logger = logging.getLogger('integrity')


class Command(BaseCommand):
    help = 'Integrity check on random objects'

    @log_command(command_title=FinanceConfigurations.Commands.TYPES[11][0])
    def handle(self, *args, **options):
        max_number = 150
        finance_models = apps.get_app_config('finance').get_models()
        indexed_models = {}
        index = 0
        for model in finance_models:
            indexed_models[index] = model
            index += 1
        # Choosing 1/3 of models randomly
        random_indexes = random.sample(range(0, index), int(index / 3))
        for random_index in random_indexes:
            model_objects = indexed_models[random_index].objects.all()
            model_count = model_objects.count()
            if model_count > max_number:
                model_count = max_number
            random_objects = random.choices(model_objects, k=model_count)
            for random_object in random_objects:
                if not Integrity.check(random_object):
                    logger.info(
                        f"{random_object._meta.model}: {random_object.id} is "
                        f"manipulated"
                    )
