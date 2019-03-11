from django.utils.module_loading import import_string
from .ingest_settings import UPLOAD_SETTINGS


def get_schema_headers():
    ordered_header = []

    good_table_validator = 'data_ingest.ingestors.GoodtablesValidator'
    schema = [loc for loc, val_type in UPLOAD_SETTINGS['VALIDATORS'].items()
              if val_type == good_table_validator and loc is not None]
    if schema:
        validator = import_string(good_table_validator)(name=good_table_validator, filename=schema[0])
        contents = validator.get_validator_contents()
        ordered_header = [field['name'] for field in contents.get('fields', [])]
    return ordered_header


def get_ordered_headers(headers):
    if isinstance(UPLOAD_SETTINGS['STREAM_ARGS']['headers'], list):
        return UPLOAD_SETTINGS['STREAM_ARGS']['headers']

    correct_headers = get_schema_headers()
    if correct_headers == headers:
        return headers

    working_headers = headers.copy()
    o_headers = []
    for h in correct_headers:
        if h in working_headers:
            o_headers.append(h)
            working_headers.remove(h)
    # add back header that didn't exist in the schema but in headers
    o_headers.extend(working_headers)
    return o_headers
