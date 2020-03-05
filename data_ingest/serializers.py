from . import ingest_settings
from rest_framework import serializers


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ingest_settings.upload_model_class
        fields = (
            'id',
            'created_at',
            'updated_at',
            'status',
            'status_changed_by',
            'status_changed_at',
            'submitter',
            'file_metadata',
            'validation_results',
        )
