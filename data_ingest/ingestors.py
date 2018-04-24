from collections import OrderedDict, defaultdict
import goodtables
import functools
import itertools
import io
import tabulator

from tabulator import Stream


class Ingestor:

    def __init__(self, upload):
        self.upload = upload

    def extracted(self):
        """
        An iterator of data from the upload

        This default implementation does not transform the data at all.
        Complex data sources, like spreadsheets with data in cells that aren't arranged
        in tables, will need to override it.
        """

        stream = tabulator.Stream(
            io.BytesIO(self.upload.raw), format=self.upload.file_type
        )
        stream.open()
        return stream

    def validate(self):
        result = goodtables.validate(list(self.extracted()))
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
                    "row_number": rn + 1, "errors": row_errs, "values": raw_row
                }
                table["rows"].append(row)
                if row_errs:
                    table["invalid_row_count"] += 1
                else:
                    table["valid_row_count"] += 1

            result["tables"].append(table)

        return result
