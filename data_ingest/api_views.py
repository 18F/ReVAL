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
    Apply all validators in settings to incoming data

    :param request: HTTP request
    :return: JSON describing validation results

    Accepts Content-Types: "text/csv" OR "application/json"

    CSV data is handled identically to as-if submitted via file upload.

    JSON data must an array of JSON objects whose keys are the expected
    data columns.

    Received JSON objects are converted to tabular format wherein all
    observed keys are considered headers/columns.
    """
    if request.content_type == 'application/json':
        data = to_tabular(request.data)
    else:
        data = request.data
    result = ingestors.apply_validators_to(data)
    return response.Response(result)


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
