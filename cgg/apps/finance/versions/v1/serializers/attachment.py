from rest_framework import serializers

from cgg.apps.finance.models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    file_id = serializers.CharField(required=True)

    class Meta:
        model = Attachment
        fields = ['id', 'file_id', 'created_at']
