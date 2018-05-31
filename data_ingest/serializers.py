from .models import Upload
from . import ingest_settings
from rest_framework import serializers


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ingest_settings.upload_model_class
        fields = ('id', 'status', 'created_at', 'file_metadata')


