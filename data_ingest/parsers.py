import csv
import io
from rest_framework import parsers

class CsvParser(parsers.BaseParser):
    """
    CSV parser.
    """
    media_type = 'text/csv'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Simply return a string representing the body of the request.
        """
        contents = stream.read().decode(parser_context['encoding'])
        reader = csv.DictReader(io.StringIO(contents))
        return reader
