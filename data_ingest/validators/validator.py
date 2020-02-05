import abc
import io
import re
import json
from collections import OrderedDict, defaultdict

from django.utils.module_loading import import_string
import tabulator

from .. import utils
from ..ingest_settings import UPLOAD_SETTINGS

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
