from rest_framework import parsers

from .ingest_settings import UPLOAD_SETTINGS


class CsvParser(parsers.BaseParser):
    """
    CSV parser.
    """
    media_type = 'text/csv'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Given a streamed CSV, return a dict of parameters for tabulator.Stream
        """

        return {
            'source': stream.read(),
            'format': 'csv',
            **UPLOAD_SETTINGS['STREAM_ARGS']
        }
