import csv
import functools
import io
import itertools
import json
import os.path
from collections import OrderedDict, defaultdict

import requests
from requests_file import FileAdapter

import goodtables
import tabulator
from django.conf import settings
from django.core import exceptions, files
from django.utils.module_loading import import_string
from tabulator import Stream

from .ingest_settings import UPLOAD_SETTINGS


class Ingestor:
    def __init__(self, upload):
        self.upload = upload
        self.table_schema = UPLOAD_SETTINGS['VALIDATION_SCHEMA']

    def extracted(self):
        """
        An iterator of data from the upload

        This default implementation does not transform the data at all.
        Complex data sources, like spreadsheets with data in cells that aren't arranged
        in tables, will need to override it.
        """

        stream = tabulator.Stream(
            io.BytesIO(self.upload.raw), format=self.upload.file_type)
        stream.open()
        return stream

    def validate(self):
        result = goodtables.validate(
            list(self.extracted()), schema=self.table_schema)
        result = self.format_results(result)
        return result

    def format_results(self, unformatted):
        """
        Transforms validation results to data-federation-ingest's expected format.

        The default validator (`goodtables.validate`) produces its results in a
        different format.  The desired format to transform it to looks like

            {'tables': [{'headers': ['Name', 'Title', 'salary'],
                'errors': []
                'invalid_row_count': 3,
                'rows': [{'errors': [],
                        'row_number': 2,
                        'values': ['Guido', 'BDFL', '0']},
                        {'errors': [{'code': 'blank-row',
                                    'message': 'Row 3 is completely blank'}],
                        'row_number': 3,
                        'values': []},
                        {'errors': [{'code': 'extra-value',
                                    'column-number': 4,
                                    'message': 'Row 4 has an extra value in '
                                                'column 4'}],
                        'row_number': 4,
                        'values': ['Catherine', '', '9', 'DBA']},
                        {'errors': [{'code': 'blank-row',
                                    'message': 'Row 5 is completely blank'}],
                        'row_number': 5,
                        'values': ['', '']},
                        {'errors': [],
                        'row_number': 6,
                        'values': ['Yoz', 'Engineer', '10']}],
                'valid_row_count': 2}],
            'valid': False}

        """

        result = {"valid": unformatted["valid"], "tables": []}

        for unf_tbl in unformatted["tables"]:

            # TODO: don't know what happens if the tabulator gives > 1 table
            table = {
                "valid_row_count": 0,
                "invalid_row_count": 0,
                "headers": unf_tbl["headers"],
                "rows": [],
                "errors": [],
            }

            errs = defaultdict(list)
            for err in unf_tbl["errors"]:
                rn = err.pop('row-number', None)
                if rn:
                    errs[rn].append(err)
                else:
                    table['errors'].append(err)

            header_skipped = False
            for (rn, raw_row) in enumerate(self.extracted()):
                # TODO: this does not seem like a good way to detect the header
                if (not header_skipped) and (raw_row == table["headers"]):
                    header_skipped = True
                    continue

                row_errs = errs.get(rn + 1, [])
                row = {
                    "row_number": rn + 1,
                    "errors": row_errs,
                    "values": raw_row
                }
                table["rows"].append(row)
                if row_errs:
                    table["invalid_row_count"] += 1
                else:
                    table["valid_row_count"] += 1

            result["tables"].append(table)

        return result

    def data(self):
        t0 = self.upload.validation_results['tables'][0]
        data = [
            dict(zip(t0['headers'], r['values'])) for r in t0['rows']
            if not r['errors']
        ]
        result = dict(self.upload.file_metadata)
        result[
            'rows'] = data  # warning - what if metadata contains a col "rows"?
        return result

    def flattened_data(self):
        nested_data = self.data()
        for row in nested_data.pop('rows'):
            final_row = dict(nested_data)
            final_row.update(
                row)  # warning - column headings that overlap with metadata...
            yield final_row

    def insert(self):
        # TODO: only insert if proper status
        if UPLOAD_SETTINGS['DESTINATION'].endswith('/'):
            inserter = self.inserters[UPLOAD_SETTINGS['DESTINATION_FORMAT']]
            return inserter(self)
        else:
            try:
                dest_model = import_string(UPLOAD_SETTINGS['DESTINATION'])
                return self.insert_to_model(dest_model)
            except ModuleNotFoundError:
                pass
        msg = "settings.DATA_INGEST['DESTINATION'] of {} could not be interpreted".format(
            settings.DATA_INGEST['DESTINATION'])
        raise exceptions.ImproperlyConfigured(msg)

    def insert_to_model(self, model_class):
        for row in self.flattened_data():
            instance = model_class(**row)
            instance.upload = self.upload
            instance.save()

    def insert_json(self):
        dest_directory = self.ingest_destination()
        file_path = os.path.join(dest_directory,
                                 self.upload.file.name) + '.json'
        with open(file_path, 'w') as dest_file:
            json.dump(self.data(), dest_file)

    inserters = {
        'json': insert_json,
    }

    def ingest_destination(self):
        dest = os.path.join(settings.MEDIA_ROOT,
                            UPLOAD_SETTINGS['DESTINATION'])
        try:
            files.storage.os.mkdir(dest)
        except FileExistsError:
            pass
        return dest
