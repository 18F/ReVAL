import io
import csv
import json
import logging
import os.path
import urllib.parse

import requests
import tabulator
import yaml
from django.conf import settings
from django.core import exceptions, files
from django.utils.module_loading import import_string

# forward imports
from .validators.goodtables import GoodtablesValidator  # noqa: F401
from .validators.rowwise import RowwiseValidator  # noqa: F401
from .validators.json import JsonlogicValidator, JsonlogicValidatorFailureConditions, JsonschemaValidator  # noqa: F401
from .validators.sql import SqlValidator, SqlValidatorFailureConditions  # noqa: F401
from .validators.validator import ValidatorOutput, UnsupportedContentTypeException, apply_validators_to  # noqa: F401

from .ingest_settings import UPLOAD_SETTINGS

logger = logging.getLogger(__name__)


class Ingestor:
    """The default ingestor assumes that the data source is already rectangular"""

    def __init__(self, upload):
        self.upload = upload

    def source(self):

        return {
            'source': self.upload.raw,
            'format': self.upload.file_type,
            **UPLOAD_SETTINGS['STREAM_ARGS']
        }

    def stream(self):
        """
        An iterator of data from the upload

        This default implementation does not transform the data at all.
        Complex data sources, like spreadsheets with data in cells that aren't arranged
        in tables, will need to override it.
        """

        stream = tabulator.Stream(
            io.BytesIO(self.upload.raw),
            format=self.upload.file_type,
            encoding='utf-8',
            **UPLOAD_SETTINGS['STREAM_ARGS'])
        stream.open()
        if UPLOAD_SETTINGS['OLD_HEADER_ROW'] is not None:
            if not UPLOAD_SETTINGS['HEADERS']:
                raise exceptions.ImproperlyConfigured(
                    "use DATA_INGEST['OLD_HEADER_ROW'] only with DATA_INGEST['HEADERS']"
                )
            for row in range(UPLOAD_SETTINGS['OLD_HEADER_ROW']):
                next(stream)  # discard rows before header

        return stream

    def validate(self):
        source = self.source()
        content_type = None
        if source['format'] == 'csv':
            content_type = 'text/csv'
        elif source['format'] == 'json':
            content_type = 'application/json'
        else:
            # @TODO: This will need to be revisited.
            # Right now pulling the file extension instead of actual ContentType as seen in header.  This will be
            # passed into each validator's validate method and causes an UnsupportedContentTypeException
            content_type = source['format']

        return apply_validators_to(self.source(), content_type)

    def meta_named(self, core_name):

        prefix = UPLOAD_SETTINGS['METADATA_PREFIX']
        return '{}{}'.format(prefix, core_name)

    def data(self):
        """Combines row data and file metadata from validation results"""

        t0 = self.upload.validation_results['tables'][0]
        result = {
            self.meta_named(k): v
            for (k, v) in self.upload.file_metadata.items()
        }
        result['rows'] = [{
            self.meta_named('row_number'): r['row_number'],
            self.meta_named('upload_id'): self.upload.id,
            **r['data']
        } for r in t0['rows'] if not r['errors']]
        return result

    def flattened_data(self):
        """For output into flat-file formats, squashes metadata into each row of data"""
        nested_data = self.data()
        for row in nested_data.pop('rows'):
            final_row = dict(nested_data)
            final_row.update(
                row)  # warning - column headings that overlap with metadata...
            yield final_row

    @classmethod
    def get_inserter(cls):
        inserter_name = 'insert_%s' % UPLOAD_SETTINGS['DESTINATION_FORMAT'].lower(
        )
        try:
            getattr(cls, inserter_name)
        except AttributeError:
            raise AttributeError(
                """UPLOAD_SETTINGS['DESTINATION_FORMAT'] %s requires method %s,
                                    which is missing from %s""" %
                (UPLOAD_SETTINGS['DESTINATION_FORMAT'], inserter_name,
                 UPLOAD_SETTINGS['INGESTOR']))

    def insert(self):
        dest = UPLOAD_SETTINGS['DESTINATION']
        if '/' in dest:
            if urllib.parse.urlparse(dest).scheme:
                resp = requests.post(dest, json=self.data())
                resp.raise_for_status()
                return resp
            # save to a directory
            inserter = getattr(
                self, 'insert_%s' % UPLOAD_SETTINGS['DESTINATION_FORMAT'])
            return inserter()
        else:
            # save to a Django model
            try:
                dest_model = import_string(dest)
                return self.insert_to_model(dest_model)
            except ModuleNotFoundError:
                pass
        msg = "DATA_INGEST['DESTINATION'] of {} could not be interpreted".format(
            dest)
        raise exceptions.ImproperlyConfigured(msg)

    def insert_to_model(self, model_class):
        for row in self.flattened_data():
            instance = model_class(**row)
            instance.upload = self.upload
            instance.save()

    def insert_json(self):
        file_path = self.ingest_destination('.json')
        with open(file_path, 'w') as dest_file:
            json.dump(self.data(), dest_file)

    def insert_yaml(self):
        file_path = self.ingest_destination('.csv')
        with open(file_path, 'w') as dest_file:
            yaml.dump(self.data(), dest_file)

    def insert_csv(self):
        file_path = self.ingest_destination('.csv')
        flat = list(self.flattened_data())
        if flat:
            keys = list(flat[0].keys())
            with open(file_path, 'w') as dest_file:
                writer = csv.DictWriter(dest_file, fieldnames=keys)
                writer.writeheader()
                writer.writerows(flat)

    # inserters = {
    #     'json': insert_json,
    #     'yaml': insert_yaml,
    # }

    def ingest_destination(self, extension):
        dest_directory = os.path.join(settings.MEDIA_ROOT,
                                      UPLOAD_SETTINGS['DESTINATION'])
        try:
            files.storage.os.mkdir(dest_directory)
        except FileExistsError:
            pass
        file_path = os.path.join(dest_directory,
                                 self.upload.file.name) + extension
        return file_path
