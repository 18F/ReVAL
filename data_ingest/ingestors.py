import abc
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
import jsonschema
import requests
import tabulator
import yaml
from django.conf import settings
from django.core import exceptions, files
from django.utils.module_loading import import_string

from .ingest_settings import UPLOAD_SETTINGS
from . import utils

logger = logging.getLogger(__name__)


###########################################
#  Helper functions to manage validators
###########################################
def validators():
    """
    Generates Validator instances based on settings.py:UPLOAD_SETTINGS['VALIDATORS']

    :return: Iterator of Validator instances

    """
    for (filename, validator_type) in UPLOAD_SETTINGS['VALIDATORS'].items():
        validator = import_string(validator_type)(
            name=validator_type, filename=filename)
        yield validator


def apply_validators_to(source, content_type):

    overall_result = {}
    for validator in validators():
        validation_results = validator.validate(source, content_type)
        overall_result = ValidatorOutput.combine(overall_result, validation_results)
    return overall_result


###########################################
#  Exception
###########################################
class UnsupportedException(Exception):
    pass


class UnsupportedContentTypeException(UnsupportedException):
    def __init__(self, content_type, validator_name):
        super(UnsupportedContentTypeException, self).__init__('Content type {} is not supported by {}'
                                                              .format(content_type, validator_name))
        self.content_type = content_type
        self.validator_name = validator_name


###########################################
#  Validator Output
###########################################
class ValidatorOutput:
    """
    This class will be used to create a standard validator output.  Validator should make use of this class
    to generate the standard validator output and its other functionalities to combine output if using more
    than one validator at a time
    """

    def __init__(self, rows_in_dict, headers=[]):
        """
        Init - Initiate objects to generate output later

        Parameters:
        rows_in_dict - a list of rows of the source.  Each row is a dictionary that consist of the row data.
                       Each row dictionary consists of `row_number` which is integer, and `row_data` which is
                       an ordered dictionary the data (key - header/field name, value - data of that field)
        headers - (optional) a list of field names in the source (if relevant, i.e. tabular data)
        """
        self.rows_in_dict = rows_in_dict
        self.headers = headers
        self.row_errors = defaultdict(list)
        self.whole_table_errors = []

    def create_error(self, severity, code, message, fields):
        """
        Create standardized error dictionary

        Parameters:
        severity - severity of this error, right now "Error" or "Warning"
        code - error code
        message - error message that describe what the error is
        fields - a list of all the field names that are associated with this error

        Returns:
        Dictionary with the following items: severity, code, message, fields
        """
        error = {}
        error["severity"] = severity
        error["code"] = code
        error["message"] = message
        error["fields"] = fields

        return error

    def add_row_error(self, row_number, severity, code, message, fields):
        """
        Add row specific error to the list of row errors

        Parameters:
        row_number - the number indicate which row this error belongs
        severity - severity of this error, right now "Error" or "Warning"
        code - error code
        message - error message that describe what the error is
        fields - a list of all the field names that are associated with this error

        Returns:
        None
        """
        error = self.create_error(severity, code, message, fields)

        self.row_errors[row_number].append(error)

    def add_whole_table_error(self, severity, code, message, fields):
        """
        Add error that applies to the whole table to the list of whole table errors

        Parameters:
        severity - severity of this error, right now "Error" or "Warning"
        code - error code
        message - error message that describe what the error is
        fields - a list of all the field names that are associated with this error

        Returns:
        None
        """
        error = self.create_error(severity, code, message, fields)

        self.whole_table_errors.append(error)

    def create_rows(self):
        """
        Create a list of row dictionary to indicates the errors it has

        Parameters:
        None

        Returns:
        A list of row dictionary
        - row dictionary consists of the following items:
          - row_number - a number to indicate the row
          - errors - a list of error dictionaries for this row
            - error - each error should match the specification from `create_error`
          - data - a dictionary of key (field name) / value (data for that field) pairs
        """
        result = []

        # Right now if we are using JsonschemaValidator, the rows_in_dict is a raw source and it will always be a list
        # of JSON object.  See validate method in JsonschemaValidator when instantiating the ValidatorOutput.  This is
        # different than the expected rows_in_dict described in the ValidatorOutput.__init__ method, where each object
        # of the list include a tuple of row_number and row_data.  So by doing the `enumerate`, it will mimic that
        # behaviors.  It also means that when using JsonschemaValidator, the row number starts at 0.

        # @TODO: Need to revisit this to see if this is the best way to do this
        rows = self.rows_in_dict.items() if isinstance(self.rows_in_dict, dict) else enumerate(self.rows_in_dict)
        for (row_number, row_data) in rows:
            result.append({
                "row_number": row_number,
                "errors": self.row_errors.get(row_number, []),
                "data": row_data
            })

        return result

    def get_output(self):
        """
        Generate the validation output based on stored values

        Parameters:
        None

        Returns:
        A dictionary with the following items:
        - tables - a list of table object
          - table - a dictionary with the following items:
            - headers - a list of field names for the data
            - whole_table_errors - a list of errors that are related to the entire table
            - rows - a dictionary generated from `create_rows`.  See specification there.
            - valid_row_count - an integer indicates the number of valid rows in the data
            - invalid_row_count - an integer indicates the number of invalid rows in the data
        - valid - boolean to indicates whether the data is valid or not
        """
        table = {}
        table["headers"] = self.headers
        table["whole_table_errors"] = self.whole_table_errors
        table["rows"] = self.create_rows()
        table["valid_row_count"] = [(not row["errors"]) for row in table["rows"]].count(True)
        table["invalid_row_count"] = len(table["rows"]) - table["valid_row_count"]

        # This needs to evaluate again at some point if this is even possible to run validator for more than
        # one table other than using GoodTables, the old code didn't allow more than one table, so should we
        # even need a list of tables?
        result = {}
        result["tables"] = [table]
        result["valid"] = (table["invalid_row_count"] == 0) and not table["whole_table_errors"]

        return result

    @staticmethod
    def combine(output1, output2):
        """
        Combine two validation outputs together.  This function expects validation outputs that follows
        the specification indicated in `get_output`

        Parameters:
        output1 - validation output that follows the spec in `get_output`
        output2 - validation output that follows the spec in `get_output`

        Returns:
        A dictionary with the same specification as `get_output` output
        """
        if not output1:
            return output2
        elif not output2:
            return output1

        table = {}
        table["headers"] = output1["tables"][0]["headers"]
        table["whole_table_errors"] = output1['tables'][0]['whole_table_errors'] + \
            output2['tables'][0]['whole_table_errors']
        table["rows"] = []

        # Will assume output1 and output2 have the same number of rows, else you will get unexpected behaviors
        for (row_number, row) in enumerate(output1['tables'][0]['rows']):
            table["rows"].append({
                "row_number": row['row_number'],
                "errors": row['errors'] + output2['tables'][0]['rows'][row_number]['errors'],
                "data": row['data']
            })

        table["valid_row_count"] = [(not row["errors"]) for row in table["rows"]].count(True)
        table["invalid_row_count"] = len(table["rows"]) - table["valid_row_count"]

        result = {}
        result["tables"] = [table]
        result["valid"] = (table["invalid_row_count"] == 0) and not table["whole_table_errors"]

        return result


###########################################
#  Validators
###########################################
class Validator(abc.ABC):

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
                "Listing ['STREAM_ARGS']['headers'] not supported by this validator (" +
                type(self).__name__ + ")"
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

    @staticmethod
    def rows_from_source(raw_source):
        source = raw_source.copy()
        try:
            f_source = io.BytesIO(source['source'])
            byteslike = True
        except (TypeError, AttributeError, KeyError):
            byteslike = False

        if byteslike:
            source['source'] = f_source
            stream = tabulator.Stream(**source, encoding='utf-8')
        else:
            stream = tabulator.Stream(source, headers=1, encoding='utf-8')

        stream.open()

        # This will get the first row
        try:
            hs = next(stream.iter(extended=True))[1]
        # nothing in the stream
        except StopIteration:
            hs = []
        # Reset the pointer to the beginning
        stream.reset()
        o_headers = utils.get_ordered_headers(hs)

        result = OrderedDict()
        for (row_num, headers, vals) in stream.iter(extended=True):
            data = dict(zip(headers, vals))
            o_data = OrderedDict((h, data.get(h, '')) for h in o_headers)
            result[row_num] = o_data

        return(o_headers, result)

    @abc.abstractmethod
    def validate(self, source, content_type):
        """
        Validate the data from source and return a standard validation output

        Parameters:
        source - raw source

        Returns:
        A dictionary object that follows the specification of `ValidatorOutput.get_output`
        """


class GoodtablesValidator(Validator):

    def validate(self, source, content_type):

        if content_type == 'application/json':
            data = utils.to_tabular(source)
        elif content_type == 'text/csv':
            data = utils.reorder_csv(source)
        else:
            raise UnsupportedContentTypeException(content_type, type(self).__name__)

        try:
            data['source'].decode()
            byteslike = True
        except (TypeError, KeyError, AttributeError):
            byteslike = False

        if byteslike:
            validate_params = data.copy()
            validate_params['schema'] = self.validator
            validate_params['source'] = io.BytesIO(data['source'])
        else:
            validate_params = {'source': data, 'schema': self.validator, "headers": 1}

        result = goodtables.validate(**validate_params)
        return self.formatted(data, result)

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
                                                'column 4 (DBA)'}],
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
        if len(unformatted["tables"]) > 1:
            raise UnsupportedException('Input with > 1 table not supported.')

        unformatted_table = unformatted["tables"][0]
        (headers, rows) = Validator.rows_from_source(source)
        output = ValidatorOutput(rows, headers=unformatted_table.get("headers", []))

        for err in unformatted_table["errors"]:
            fields = []
            message = err['message']
            # This is to include the header name with the column number and to define fields
            if err.get('column-number'):
                column_number = err['column-number']
                if len(headers) >= column_number:
                    header = headers[column_number - 1]
                    fields = [header]
                    column_num = 'column ' + str(column_number)
                    message = err['message'].replace(column_num, column_num + ' (' + header + ')')

            if err.get('row-number'):
                output.add_row_error(err['row-number'], "Error", err["code"], message, fields)
            else:
                output.add_whole_table_error("Error", err["code"], message, fields)

        return output.get_output()


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

    @staticmethod
    def cast_value(value):
        """
        This will help clean the value and cast the value to its type
        i.e. "123" is an integer, so it will be casted to become 123

        Parameters:
        value - a string that needs to be casted

        Returns:
        a value that has been processed and casted to its type (string, integer, or float)
        """
        newval = value
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

        return newval

    @staticmethod
    def cast_values(row_values):
        """
        This will help clean up a list of data and cast them to numbers when appropriate

        Parameters:
        row_values - a list of values

        Returns:
        a list of casted values
        """
        return [RowwiseValidator.cast_value(value) for value in row_values]

    @staticmethod
    def replace_message(message, row_dict):
        """
        String Intepolation for message.  Anything that is included inside the curly brackets {} will
        be evaluated and replaced by its value.

        - {column}: By putting the column name inside the curly brackets, this will be replaced with the
          actual value of this row's column.
        - {A op B}: A is a column name or a number (integer or decimal number), op is an arithmetic operator
          +, -, * or /, and B is a column name or a number (integer or decimal number).
        - {A op B:C}: A op B is the same as above, C is the number of decimal places to display after the decimal.

        Parameters:
        message - a string
        row_dict - a dictionary of key(field name) / value(field data) pair

        Returns:
        string - a new message with content in {} replaced

        """
        # create message
        new_message = message
        # Pattern that will match everything that looks like this: {...}
        pattern = re.compile(r'\{.*?\}')
        fields = pattern.findall(new_message)
        for field in fields:
            # Remove { }
            key = field[1:-1].strip()
            # Direct Substitution
            if key in row_dict.keys():
                new_message = new_message.replace(field, row_dict[key])
            # Expression Calculation and Substitution
            else:
                # This will put out the two field names (strip out any spaces), and the operator
                # and the rest of field to check for precision specification
                # (operand1 operator operand2 rest)
                # current supported operator is seen in the 2nd parenthesis
                expression = re.match(r'^\s*(\S+)\s*([\+\-\*/])\s*([^:\s]+)(\S*)\s*$', key)

                try:
                    # only supporting int/float operations
                    supported_type = (float, int)
                    operand1, operator, operand2, rest = expression.groups()

                    # If operands are numbers
                    value1 = RowwiseValidator.cast_value(operand1)
                    value2 = RowwiseValidator.cast_value(operand2)

                    # If operands are not numbers, they may be key to row_dict, get the real values
                    if not any(isinstance(value1, t) for t in supported_type):
                        value1 = RowwiseValidator.cast_value(row_dict[operand1])

                    if not any(isinstance(value2, t) for t in supported_type):
                        value2 = RowwiseValidator.cast_value(row_dict[operand2])

                    # If they are all supported type, then this expression can be evaluated
                    if any(isinstance(value1, t) for t in supported_type) and \
                       any(isinstance(value2, t) for t in supported_type):
                        # Right now being super explicit about which operator we support
                        if operator == '+':
                            result = value1 + value2
                        elif operator == '-':
                            result = value1 - value2
                        elif operator == '*':
                            result = value1 * value2
                        elif operator == '/':
                            result = value1 / value2
                        else:
                            # it really shouldn't have gotten here because we are only matching the allowed
                            # operation above
                            raise UnsupportedException()

                        # Will only use this when we are very sure there is no issue
                        # result = eval(f'{value1} {operator} {value2}')

                        # If precision is supplied, the "rest" should include this information in the following form:
                        # ':number_of_digits_after_decimal_place'
                        if rest:
                            if len(rest) > 1 and rest[0] == ':':
                                precision = int(rest[1:])
                                result = f'{result:.{precision}f}'
                            else:
                                # This means this is malformed
                                raise ValueError

                        new_message = new_message.replace(field, str(result))

                except (KeyError, AttributeError, ValueError):
                    # This means the expression is malformed or key are misspelled
                    new_message = f"Unable to evaluate {field}"
                    break
                except UnsupportedException:
                    new_message = f"Unsupported operation in {field}"
                    break

        return new_message

    def validate(self, source, content_type):
        """
        Implemented validate method
        """

        if content_type == 'application/json':
            data = utils.to_tabular(source)
        elif content_type == 'text/csv':
            data = utils.reorder_csv(source)
        else:
            raise UnsupportedContentTypeException(content_type, type(self).__name__)

        (headers, numbered_rows) = Validator.rows_from_source(data)
        output = ValidatorOutput(numbered_rows, headers=headers)

        for (rn, row) in numbered_rows.items():

            # This is to remove the header row
            if rn == UPLOAD_SETTINGS['OLD_HEADER_ROW']:
                continue

            # Check for columns required by validator
            received_columns = set(headers)
            for rule in self.validator:
                expected_columns = set(rule['columns'])
                missing_columns = expected_columns.difference(received_columns)
                if missing_columns:
                    output.add_row_error(rn, 'Error', rule.get('error_code'),
                                         f'Unable to evaluate, missing columns: {missing_columns}', [])
                    continue
                try:
                    if rule['code'] and not self.invert_if_needed(self.evaluate(rule['code'], row)):

                        output.add_row_error(rn,
                                             rule.get('severity', 'Error'),
                                             rule.get('error_code'),
                                             RowwiseValidator.replace_message(rule.get('message', ''), row),
                                             [
                                                k for (idx, k) in enumerate(row.keys())
                                                if k in rule['columns']
                                             ]
                                             )
                except Exception as e:
                    output.add_row_error(rn, 'Error', rule.get('error_code'),
                                         f'{type(e).__name__}: {e.args[0]}', [])
        return output.get_output()

    @abc.abstractmethod
    def evaluate(self, rule, row):
        """
        Evaluate the row based on the rule

        Parameters:
        rule - the rule that needs to apply to the row
        row - the dictionary of key(field name)/value(field data) pair

        Returns:
        Boolean - True/False
        """


class JsonlogicValidator(RowwiseValidator):
    def evaluate(self, rule, row):
        return json_logic.jsonLogic(rule, row)


class JsonlogicValidatorFailureConditions(JsonlogicValidator):
    """
    Like JsonlogicValidator, but rules express failure conditions, not success
    """

    INVERT_LOGIC = True


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

        cvalues = SqlValidator.cast_values(row.values())

        self.db_cursor.execute(sql, tuple(cvalues))
        result = self.db_cursor.fetchone()[0]

        return bool(result)


class SqlValidatorFailureConditions(SqlValidator):
    """
    Like SqlValidator, but rules express failure conditions, not success
    """

    INVERT_LOGIC = True


class JsonschemaValidator(Validator):

    def validate(self, source, content_type):
        if content_type != "application/json":
            raise UnsupportedContentTypeException(content_type, type(self).__name__)

        # Find the correct version of the validator to use for this schema
        json_validator = jsonschema.validators.validator_for(self.validator)(self.validator)

        # Check the schema to make sure there's no error
        json_validator.check_schema(self.validator)

        if type(source) is list:  # validating an array (list) of objects
            output = ValidatorOutput(source)
        else:  # validating only one object but making it a list of objects
            output = ValidatorOutput([source])

        errors = json_validator.iter_errors(source)

        for error in errors:
            if error.path:
                output.add_row_error(error.path[0], "Error", error.validator, error.message, list(error.path)[1:])
            else:
                output.add_row_error(0, "Error", error.validator, error.message, [])

        return output.get_output()


###########################################
#  Ingestor
###########################################
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
