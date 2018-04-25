
import deep_merge
from django.conf import settings
from django.utils.module_loading import import_string

DEFAULT_UPLOAD_SETTINGS = { 'FORM': 'data_ingest.forms.UploadForm',
    'INGESTOR': 'data_ingest.ingestors.Ingestor',
    'TEMPLATE': 'data_ingest/upload.html',
    'MODEL': 'data_ingest.models.Upload',
}

UPLOAD_SETTINGS = deep_merge.merge(DEFAULT_UPLOAD_SETTINGS,
    getattr(settings, 'DATA_UPLOAD', {}))


upload_form_class = import_string(UPLOAD_SETTINGS['FORM'])
model_form_class = import_string(UPLOAD_SETTINGS['MODEL'])
ingestor_class = import_string(UPLOAD_SETTINGS['INGESTOR'])
