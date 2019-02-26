import csv
import io
import json
import logging
import os.path
import re
import sqlite3
import urllib.parse
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation

import goodtables
import json_logic
import requests
import tabulator
import yaml
from django.conf import settings
from django.core import exceptions, files
from django.utils.module_loading import import_string

from .ingest_settings import UPLOAD_SETTINGS

logger = logging.getLogger(__name__)


class Validator:

    SUPPORTS_HEADER_OVERRIDE = False
    INVERT_LOGIC = False

    url_pattern = re.compile(r'^\w{3,5}://')

    def invert_if_needed(self, value):
        """
        Inverts a boolean, iff `self.INVERT_LOGIC`

        :param value: Boolean value to invert (or not)
        :return: Boolean
        """

        if self.INVERT_LOGIC:
            return not value
        else:
            return value

    def __init__(self, name, filename):
        """

        :param name: Name of the validator class
        :param filename: Name of file to load validation rules from

        """
        self.name = name
        self.filename = filename
        self.validator = self.get_validator_contents()

        if isinstance(UPLOAD_SETTINGS['STREAM_ARGS']['headers'],
                      list) and (not self.SUPPORTS_HEADER_OVERRIDE):
            raise exceptions.ImproperlyConfigured(
                "Listing ['STREAM_ARGS']['headers'] not supported by this validator"
            )

    def load_file(self):
        with open(self.filename) as infile:
            if self.filename.endswith('.yml') or self.filename.endswith(
                    '.yaml'):
                return yaml.safe_load(infile)
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
                        return yaml.safe_load(resp.text)
                    return resp.json()
                else:
                    raise exceptions.ImproperlyConfigured(
                        'validator {} {} returned {}'.format(
                            self.name, self.filename, resp.status))
            else:
                return self.load_file()
        return self.filename


def rows_from_source(raw_source):
    source = raw_source.copy()
    try:
        f_source = io.BytesIO(source['source'])
        byteslike = True
    except (TypeError, AttributeError):
        byteslike = False

    if byteslike:
        source['source'] = f_source
        stream = tabulator.Stream(**source, encoding='utf-8')
    else:
        stream = tabulator.Stream(source, headers=1, encoding='utf-8')

    stream.open()
    result = OrderedDict(
        (row_num, OrderedDict((k, v) for (k, v) in zip(headers, vals) if k))
        for (row_num, headers, vals) in stream.iter(extended=True))
    return (stream.headers, result)


class UnsupportedException(Exception):
    pass


class GoodtablesValidator(Validator):

    def validate(self, source):

        try:
            source['source'].decode()
            byteslike = True
        except (TypeError, KeyError, AttributeError):
            byteslike = False

        if byteslike:
            validate_params = source.copy()
            validate_params['schema'] = self.validator
            validate_params['source'] = io.BytesIO(source['source'])
        else:
            validate_params = {'source': source, 'schema': self.validator, "headers": 1}

        result = goodtables.validate(**validate_params)
        return self.formatted(source, result)

    def formatted(self, source, unformatted):
        """
        Transforms validation results to data-federation-ingest's expected format.

        The default validator (`goodtables.validate`) produces its results in a
        different format.  The desired format to transform it to looks like

            {'tables': [{'headers': ['Name', 'Title', 'salary'],
                'whole_table_errors': []
                'invalid_row_count': 3,
                'rows': [{'errors': [],
                        'row_number': 2,
                        'data': ['Guido', 'BDFL', '0']},
                        {'errors': [{'code': 'blank-row',
                                    'message': 'Row 3 is completely blank'}],
                        'row_number': 3,
                        'data': []},
                        {'errors': [{'code': 'extra-value',
                                    'column-number': 4,
                                    'message': 'Row 4 has an extra value in '
                                                'column 4'}],
                        'row_number': 4,
                        'data': ['Catherine', '', '9', 'DBA']},
                        {'errors': [{'code': 'blank-row',
                                    'message': 'Row 5 is completely blank'}],
                        'row_number': 5,
                        'data': ['', '']},
                        {'errors': [],
                        'row_number': 6,
                        'data': ['Yoz', 'Engineer', '10']}],
                'valid_row_count': 2}],
            'valid': False}
    ``
        """

        (headers, rows) = rows_from_source(source)
        result = {"valid": unformatted["valid"], "tables": []}

        if len(unformatted["tables"]) > 1:
            raise UnsupportedException('Input with > 1 table not supported.')

        for unformatted_table in unformatted["tables"]:

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

            for (rn, raw_row) in rows.items():

                # Assemble a description of each row
                row_errs = errs.get(rn, [])
                row = {
                    "row_number": rn,
                    "errors": row_errs,
                    "data": raw_row,
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
        'severity':
        rule.get('severity', 'Error'),
        'code':
        rule.get('error_code'),
        'message':
        rule.get('message', '').format(**row_dict),
        'error_columns': [
            k for (idx, k) in enumerate(row_dict.keys())
            if k in rule['columns']
        ]
    }


class RowwiseValidator(Validator):
    '''Subclass this for any validator applied to one row at a time.

    Rule file should be JSON or YAML with fields

    Then each subclass only needs an `evaluate(self, rule, row)`
    method returning Boolean
    '''

    SUPPORTS_HEADER_OVERRIDE = True

    if 'headers' not in UPLOAD_SETTINGS['STREAM_ARGS']:
        raise exceptions.ImproperlyConfigured(
            "setting DATA_INGEST['STREAM_ARGS']['headers'] is required")

    if UPLOAD_SETTINGS.get('OLD_HEADER_ROW') and not isinstance(
            UPLOAD_SETTINGS['STREAM_ARGS']['headers'], list):
        raise exceptions.ImproperlyConfigured(
            """DATA_INGEST['OLD_HEADER_ROW'] should be used with a
            list of headers in DATA_INGEST['STREAM_ARGS']['header']"""
        )

    def validate(self, source):

        table = {
            'invalid_row_count': 0,
            'valid_row_count': 0,
            'whole_table_errors': [],
        }

        rows = []
        (table['headers'], numbered_rows) = rows_from_source(source)
        for (rn, row) in numbered_rows.items():

            if rn == UPLOAD_SETTINGS['OLD_HEADER_ROW']:
                table['headers'] = list(row.values())
                continue

            errors = []
            # Check for columns required by validator
            received_columns = set(table['headers'])
            for rule in self.validator:
                expected_columns = set(rule['columns'])
                missing_columns = expected_columns.difference(received_columns)
                if missing_columns:
                    errors.append({'severity': 'Error',
                                   'code': rule['error_code'],
                                   'message': f'Unable to evaluate, missing columns: {missing_columns}',
                                   'error_columns': []})
                    continue
                if rule['code'] and not self.invert_if_needed(self.evaluate(rule['code'], row)):
                    errors.append(row_validation_error(rule, row))

            # errors = [
            #     row_validation_error(rule, row) for rule in self.validator
            #     if not self.invert_if_needed(self.evaluate(rule['code'], row))
            # ]
            if errors:
                table['invalid_row_count'] += 1
            else:
                table['valid_row_count'] += 1
            rows.append({
                'row_number': rn,
                'data': row,
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
    def evaluate(self, rule, row):
        return json_logic.jsonLogic(rule, row)


class JsonlogicValidatorFailureConditions(JsonlogicValidator):
    """
    Like JsonlogicValidator, but rules express failure conditions, not success
    """

    INVERT_LOGIC = True


class SqlValidator(RowwiseValidator):
    @staticmethod
    def cast_values(row_values):
        # This will help clean up the data and cast them to numbers when
        # appropriate
        # TODO: This may be a temporary fix, like to revisit to see if "type"
        # should be something defined in settings.py along with column names
        cvalues = []
        for val in row_values:
            newval = val
            if type(newval) == str:
                newval = newval.strip()
                try:
                    dnewval = Decimal(newval.replace(',', ''))
                    try:
                        inewval = int(dnewval)
                        fnewval = float(dnewval)
                        if inewval == fnewval:
                            newval = inewval
                        else:
                            newval = fnewval
                    except ValueError:
                        # will take the newval.strip() as the value
                        pass
                except InvalidOperation:
                    # will take the newval.strip() as the value
                    pass

            cvalues.append(newval)

        return cvalues

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

        cvalues = SqlValidator.cast_values(row.values())

        self.db_cursor.execute(sql, tuple(cvalues))
        result = self.db_cursor.fetchone()[0]
        return bool(result)


class SqlValidatorFailureConditions(SqlValidator):
    """
    Like SqlValidator, but rules express failure conditions, not success
    """

    INVERT_LOGIC = True


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
        results0['tables'][0]['whole_table_errors'].extend(
            results1['tables'][0]['whole_table_errors'])
        results0['valid'] = results0['valid'] and results1['valid']
        return results0
    else:
        return results1


def validators():
    """
    Generates Validator instances based on settings.py:UPLOAD_SETTINGS['VALIDATORS']

    :return: Iterator of Validator instances

    """
    for (filename, validator_type) in UPLOAD_SETTINGS['VALIDATORS'].items():
        validator = import_string(validator_type)(
            name=validator_type, filename=filename)
        yield validator


def count_valid_rows(validation_results):
    validation_results['valid_row_count'] = 0
    validation_results['invalid_row_count'] = 0
    for row in validation_results['tables'][0]['rows']:
        if row['errors']:
            validation_results['invalid_row_count'] += 1
        else:
            validation_results['valid_row_count'] += 1


def apply_validators_to(source):

    # for (rn, headers, row_vals) in stream.iter(extended=True):

    overall_result = {}
    for validator in validators():
        validation_results = validator.validate(source)
        overall_result = combine_validation_results(
            results0=overall_result, results1=validation_results)
    count_valid_rows(overall_result)
    return overall_result


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

        return apply_validators_to(self.source())

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
