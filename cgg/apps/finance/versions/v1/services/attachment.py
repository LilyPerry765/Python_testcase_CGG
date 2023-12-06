# --------------------------------------------------------------------------
# This service does not handle uploading and downloading, It's a
# pseudo-model to handle uploaded file id's. To upload and download files
# use another microservice.
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - attachment.py
# Created at 2020-8-29,  16:44:46
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from cgg.apps.finance.models import Attachment
from cgg.apps.finance.versions.v1.serializers.attachment import (
    AttachmentSerializer,
)


class AttachmentService:
    @classmethod
    def create_attachment(cls, file_id: str):
        """
        Get a file_id, create an attachment for it
        :param file_id:
        :return:
        """
        attachment_serializer = AttachmentSerializer(
            data={
                'file_id': file_id,
            }
        )
        if attachment_serializer.is_valid():
            attachment_serializer.save()

        return Attachment.objects.get(id=attachment_serializer.data['id'])
