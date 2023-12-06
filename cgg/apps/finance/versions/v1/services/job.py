# --------------------------------------------------------------------------
# Handle logics related to FailedJob objects. Depends on project's structure
# and file method names. if the structure or file names changes this service
# must changes.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - job.py
# Created at 2020-8-29,  17:23:29
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from importlib import import_module
from json import JSONDecodeError

from cgg.apps.finance.models import FailedJob
from cgg.core import api_exceptions
from cgg.core.tools import Tools


class JobService:

    @classmethod
    def import_job_module(cls, service_name, version='v1'):
        """
        Dynamically import module based on service name and version
        Depends on project's structure, file and method names
        :param service_name:
        :param version:
        :return:
        """
        try:
            service_name_module = \
                f"{Tools.camelcase_to_snake_case(service_name)}".replace(
                    '_service',
                    '',
                )
            abs_module_path = f"cgg.apps.finance.versions.{version}.services" \
                              f".{service_name_module}"
            module_object = import_module(abs_module_path)
            target_class = getattr(module_object, service_name)

            return target_class
        except ModuleNotFoundError:
            return False

    @classmethod
    def redo_the_job(cls, job_object):
        """
        Redo the job based on method and service
        Depends on project's structure, file and method name
        :param job_object: an object from FailedJob model
        :return: True if successful and False otherwise
        """
        if not job_object.is_done:
            try:
                service = cls.import_job_module(
                    job_object.service_name,
                    job_object.service_version,
                )
                method_args = Tools.get_dict_from_json(job_object.method_args)
                method = getattr(service, job_object.method_name)(
                    **method_args,
                )

                if method:
                    job_object.is_done = True
                    job_object.save()

                    return True

                return False
            except (JSONDecodeError, ValueError, api_exceptions.APIException):
                return False

        return False

    @classmethod
    def add_failed_job(
            cls,
            job_title,
            service_version,
            service_name,
            method_name,
            method_args,
            error_message='',
    ):
        """
        Add new object to failed jobs
        Depends on project's structure, file and method name
        :param job_title:
        :param service_version:
        :param service_name:
        :param method_name:
        :param method_args:
        :param error_message:
        :return:
        """
        failed_job_object = FailedJob()
        failed_job_object.job_title = job_title
        failed_job_object.service_version = service_version
        failed_job_object.service_name = service_name
        failed_job_object.method_name = method_name
        failed_job_object.method_args = method_args
        failed_job_object.error_message = error_message
        failed_job_object.save()
