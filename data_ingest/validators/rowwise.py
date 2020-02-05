import abc
import re
from decimal import Decimal, InvalidOperation

import tabulator

from .validator import Validator, ValidatorOutput, UnsupportedContentTypeException
from ..ingest_settings import UPLOAD_SETTINGS
from .. import utils

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
