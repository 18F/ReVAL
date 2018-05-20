from django.conf import settings
from django.utils.module_loading import import_string

DEFAULT_UPLOAD_SETTINGS = {
    'FORM': 'data_ingest.forms.UploadForm',
    'INGESTOR': 'data_ingest.ingestors.Ingestor',
    'TEMPLATE': 'data_ingest/upload.html',
    'LIST_TEMPLATE': 'data_ingest/upload_list.html',
    'DETAIL_TEMPLATE': 'data_ingest/upload_detail.html',
    'MODEL': 'data_ingest.models.DefaultUpload',
    'DESTINATION': 'data_ingest/',
    'DESTINATION_FORMAT': 'json',
    'VALIDATORS': {
        None: 'data_ingest.ingestors.GoodtablesValidator',
    },
}

UPLOAD_SETTINGS = dict(DEFAULT_UPLOAD_SETTINGS)
UPLOAD_SETTINGS.update(getattr(settings, 'DATA_INGEST', {}))

upload_form_class = import_string(UPLOAD_SETTINGS['FORM'])
upload_model_class = import_string(UPLOAD_SETTINGS['MODEL'])
ingestor_class = import_string(UPLOAD_SETTINGS['INGESTOR'])
