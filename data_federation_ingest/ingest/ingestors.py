from collections import OrderedDict
import goodtables
import functools
import itertools
import io
import tabulator

from tabulator import Stream
stream = Stream('has-blanks.csv')
stream.open()
list(stream)

class Ingestor:

    @classmethod
    def extract(cls, raw):
        """
        Extracts data from raw source to a form readable by frictionlessdata/tabulator-py, like JSON

        This default implementation does not transform the data at all.
        Complex data sources, like spreadsheets with data in cells that aren't arranged
        in tables, will need to override it.
        """

        # TODO: remove blank rows

        return raw

    @classmethod
    def add_rows(cls, validation_results, upload):

        table = validation_results['tables'][0]  # TODO: deal with >1 tables?
        stream = tabulator.Stream(io.BytesIO(upload.extracted), format=upload.file_type)
        stream.open()
        table['rows'] = [{'valid': True,
            'data': OrderedDict(itertools.zip_longest(table['headers'], raw_row)),
            'raw': raw_row, }
            for raw_row in stream]
        for error in table['errors']:
            if 'row-number' in error:
                rn = error.pop('row-number')  # hyphens bad in dj templates
                error['row_number'] = rn
                row = table['rows'][rn-1]
                row['valid'] = False
                error['row'] = row['data']
                error['raw_row'] = row['raw']
        table['valid_row_count'] = len([r for r in table['rows'] if r['valid']])
        table['invalid_row_count'] = table['row-count'] - table['valid_row_count']
        validation_results['table'] = table
        validation_results.pop('tables')
        return validation_results

    @classmethod
    def validate(cls, upload, *args, **kwargs):
        result = goodtables.validate(io.BytesIO(upload.extracted), format=upload.file_type)
        result = cls.add_rows(result, upload)
        return result


