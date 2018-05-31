import io
import json
import logging
import os.path
import re
import sqlite3
from collections import defaultdict

import goodtables
import json_logic
import requests
import tabulator
import yaml
from django.conf import settings
from django.core import exceptions, files
from django.utils.module_loading import import_string
from tabulator import Stream

from .ingest_settings import UPLOAD_SETTINGS

logger = logging.getLogger(__name__)


class Validator:

    url_pattern = re.compile(r'^\w{3,5}://')

    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.validator = self.get_validator_contents()

    def load_file(self):
        with open(self.filename) as infile:
            if self.filename.endswith('.yml') or self.filename.endswith(
                    '.yaml'):
                return yaml.load(infile)
            else:
                return json.load(infile)

    def get_validator_contents(self):
        """Return validator filename, or URL contents in case of URLs"""

        if self.filename:
            if self.url_pattern.search(self.filename):
                resp = requests.get(self.filename)
                if resp.ok:
                    if self.filename.endswith('yml') or self.filename.endswith(
                            '.yaml'):
                        return yaml.load(resp.text)
                    return resp.json()
                else:
                    raise exceptions.ImproperlyConfigured(
                        'validator {} {} returned {}'.format(
                            self.name, self.filename, resp.status))
            else:
                return self.load_file()
        return self.filename


class GoodtablesValidator(Validator):
    def validate(self, data):

        result = goodtables.validate(data, schema=self.validator)
        t0 = result['tables'][0]
        return self.formatted(data, result)

    def formatted(self, data, unformatted):
        """
        Transforms validation results to data-federation-ingest's expected format.

        The default validator (`goodtables.validate`) produces its results in a
        different format.  The desired format to transform it to looks like

            {'tables': [{'headers': ['Name', 'Title', 'salary'],
                'whole_table_errors': []
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

        for unformatted_table in unformatted["tables"]:

            # TODO: don't know what happens if the tabulator gives > 1 table
            table = {
                "valid_row_count": 0,
                "invalid_row_count": 0,
                "headers": unformatted_table["headers"],
                "rows": [],
                "whole_table_errors": [],
            }

            # Produce a dictionary of errors by row number
            errs = defaultdict(list)
            for err in unformatted_table["errors"]:
                rn = err.pop('row-number', None)
                if rn:
                    errs[rn].append(err)
                else:
                    table['whole_table_errors'].append(err)
                    result['valid'] = False

            header_skipped = False
            for (rn, raw_row) in enumerate(data):
                # TODO: this does not seem like a good way to detect the header
                if (not header_skipped) and (raw_row == table["headers"]):
                    header_skipped = True
                    continue

                # Assemble a description of each row
                row_errs = errs.get(
                    rn + 1,
                    [])  # We report row numbers in 1-based, not 0-based
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


def row_validation_error(rule, row_dict):
    """Dictionary describing a single row validation error"""

    return {
        'severity': rule.get('severity', 'Error'),
        'code': rule.get('error_code'),
        'message': rule.get('message', '').format(**row_dict),
        'error_columns': [
            idx
            for (idx, k) in enumerate(row_dict.keys()) if k in rule['columns']
        ]
    }


class RowwiseValidator(Validator):
    '''Subclass this for any validator applied to one row at a time.

    Rule file should be JSON or YAML with fields

    {'Text describing rule': <rule>
     ...
    }

    Then each subclass only needs an `evaluate(self, rule, row)`
    method returning Boolean
    '''

    def validate(self, data):

        table = {
            'headers': [],
            'invalid_row_count': 0,
            'valid_row_count': 0,
            'whole_table_errors': [],
        }

        rows = []

        for (raw_rn, row) in enumerate(data):
            if (not table['headers']) and (any(row)):
                table['headers'] = row
                continue
            errors = []
            row_dict = dict(zip(table['headers'], row))
            for rule in self.validator:
                result = self.evaluate(rule['code'], row_dict)
                if not result:
                    errors.append(row_validation_error(rule, row_dict))
            if errors:
                table['invalid_row_count'] += 1
            else:
                table['valid_row_count'] += 1
            rows.append({
                'row_number': raw_rn + 1,
                'values': row,
                'errors': errors,
            })
        table['rows'] = rows

        result = {
            'tables': [
                table,
            ],
            'valid': (table['invalid_row_count'] == 0)
        }
        return result


class JsonlogicValidator(RowwiseValidator):
    def valid_row(self, rule, row):
        return json_logic.jsonLogic(rule, row)


class SqlValidator(RowwiseValidator):
    def __init__(self, *args, **kwargs):

        self.db = sqlite3.connect(':memory:')
        self.db_cursor = self.db.cursor()
        return super().__init__(*args, **kwargs)

    def first_statement_only(self, sql):
        'Discard any second sql statement, just as from a sql injection'

        # Very simplistic SQL injection protection, but the attack would
        # have to come from the rule-writer, and the database contains no
        # data anyway
        return sql.split(';')[0]

    def evaluate(self, rule, row):

        if not rule:
            return True  # rule not implemented

        aliases = [' ? as {} '.format(col_name) for col_name in row.keys()]
        aliases = ','.join(aliases)

        sql = f"select {rule} from ( select {aliases} )"
        sql = self.first_statement_only(sql)

        self.db_cursor.execute(sql, tuple(row.values()))

        return bool(self.db_cursor.fetchone()[0])


def combine_validation_results(results0, results1):
    """
    Adds two dictionaries of validation results, meshing row-wise results

    :param results0: A dictionary of validation results.  Will be mutated.
    :param results1: A dictionary to be added to results0
    :return: results0 with results included
    """
    if results0:
        for (rn, row) in enumerate(results0['tables'][0]['rows']):
            row['errors'].extend(results1['tables'][0]['rows'][rn]['errors'])
        results0['tables'][0]['whole_table_errors'].extend(results1['tables'][
            0]['whole_table_errors'])
        results0['valid'] = results0['valid'] and results1['valid']
        return results0
    else:
        return results1


def validators():
    """
    Generates Validator instances based on settings.py:UPLOAD_SETTINGS['VALIDATORS']

    :return: Iterator of Validator instances

    """
    for (filename, type) in UPLOAD_SETTINGS['VALIDATORS'].items():
        validator = import_string(type)(name=type, filename=filename)
        yield validator


def apply_validators_to(data):

    overall_result = {}
    for validator in validators():
        validation_results = validator.validate(data)
        overall_result = combine_validation_results(
            results0=overall_result,
            results1=validation_results)
    return overall_result


class Ingestor:
    """The default ingestor assumes that the data source is already rectangular"""

    def __init__(self, upload):
        self.upload = upload

    def extracted(self):
        """
        An iterator of data from the upload

        This default implementation does not transform the data at all.
        Complex data sources, like spreadsheets with data in cells that aren't arranged
        in tables, will need to override it.
        """

        stream_args = settings.DATA_INGEST.get('STREAM_ARGS', {})
        stream = tabulator.Stream(
            io.BytesIO(self.upload.raw),
            format=self.upload.file_type,
            **stream_args)
        stream.open()
        return stream

    def validate(self):

        data = list(self.extracted())
        result = apply_validators_to(data)

    def data(self):
        t0 = self.upload.validation_results['tables'][0]
        data = [
            dict(zip(t0['headers'], r['values']))
            for r in t0['rows'] if not r['errors']
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

    inserters = {'json': insert_json, }

    def ingest_destination(self):
        dest = os.path.join(settings.MEDIA_ROOT,
                            UPLOAD_SETTINGS['DESTINATION'])
        try:
            files.storage.os.mkdir(dest)
        except FileExistsError:
            pass
        return dest
