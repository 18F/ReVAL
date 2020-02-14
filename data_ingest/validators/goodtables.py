import io

import goodtables

from .validator import (
    Validator,
    ValidatorOutput,
    UnsupportedException,
    UnsupportedContentTypeException,
)
from .. import utils


class GoodtablesValidator(Validator):
    def validate(self, source, content_type):

        if content_type == "application/json":
            data = utils.to_tabular(source)
        elif content_type == "text/csv":
            data = utils.reorder_csv(source)
        else:
            raise UnsupportedContentTypeException(content_type, type(self).__name__)

        try:
            data["source"].decode()
            byteslike = True
        except (TypeError, KeyError, AttributeError):
            byteslike = False

        if byteslike:
            validate_params = data.copy()
            validate_params["schema"] = self.validator
            validate_params["source"] = io.BytesIO(data["source"])
        else:
            validate_params = {"source": data, "schema": self.validator, "headers": 1}

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
            raise UnsupportedException("Input with > 1 table not supported.")

        unformatted_table = unformatted["tables"][0]
        (headers, rows) = Validator.rows_from_source(source)
        output = ValidatorOutput(rows, headers=unformatted_table.get("headers", []))

        for err in unformatted_table["errors"]:
            fields = []
            message = err["message"]
            # This is to include the header name with the column number and to define fields
            if err.get("column-number"):
                column_number = err["column-number"]
                if len(headers) >= column_number:
                    header = headers[column_number - 1]
                    fields = [header]
                    column_num = "column " + str(column_number)
                    message = err["message"].replace(
                        column_num, column_num + " (" + header + ")"
                    )

            if err.get("row-number"):
                output.add_row_error(
                    err["row-number"], "Error", err["code"], message, fields
                )
            else:
                output.add_whole_table_error("Error", err["code"], message, fields)

        return output.get_output()
