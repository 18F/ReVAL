from django.views.decorators.csrf import csrf_exempt
from rest_framework import decorators, response, viewsets
from rest_framework.parsers import JSONParser

from . import ingest_settings, ingestors
from .parsers import CsvParser
from .serializers import UploadSerializer

import logging

logger = logging.getLogger(__name__)

class UploadViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ingest_settings.upload_model_class.objects.all().order_by(
        'created_at')
    serializer_class = UploadSerializer


@csrf_exempt
@decorators.api_view(['POST'])
@decorators.parser_classes((JSONParser, CsvParser))
def validate(request):
    """
    Apply all validators in settings to JSON data

    :param request: HTTP request
    :return: JSON describing validation results

    to post a CSV:
        curl - X POST - H "Content-Type: text/csv" --data-binary @myfile.csv https://...
        # omitting --data-binary strips newlines!

    or

        import requests
        url = 'http://localhost:8000/data_ingest/api/validate/'
        with open('test_cases.csv') as infile:
            content = infile.read()
        resp = requests.post(url, data=content, headers={"Content-Type": "text/csv"})

    """
    if request.content_type == 'application/json':
        data = to_tabular(request.data)
    else:
        data = request.data
    result = ingestors.apply_validators_to(data)
    return response.Response(result)

    # to use: curl - X POST - H "Content-Type: text/csv" --data-binary @myfile.csv https://...
    # omitting --data-binary strips newlines!


def to_tabular(incoming):
    """Coerce incoming json to tabular structure for tabulator
    [
        [All observed keys(headers)],
        [values],
        [values],
        ...
    ]

    First list contains all observed `columns`, following lists
    are data rows containing data values in the order of headers defined
    in the first row.
    """
    headers = set()
    for row in incoming:
        for header in row.keys():
            headers.add(header)

    headers = list(headers)
    output = [headers]
    for row in incoming:
        row_data = []
        for header in headers:
            logger.debug(f"Fetching: {header}")
            val = row.get(header, None)
            row_data.append(val)
            logger.debug(f'Set to: {val}')
        output.append(row_data)
    return output
