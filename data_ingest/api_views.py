import csv
import io
import logging

from collections import OrderedDict
from django.views.decorators.csrf import csrf_exempt
from rest_framework import decorators, response, viewsets
from rest_framework.parsers import JSONParser

from . import ingest_settings, ingestors
from .parsers import CsvParser
from .serializers import UploadSerializer
from .utils import get_ordered_headers


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
    elif request.content_type == 'text/csv':
        # data = request.data
        data = reorder_csv(request.data)
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

    o_headers = get_ordered_headers(headers)

    output = [o_headers]
    for row in incoming:
        row_data = []
        for header in o_headers:
            logger.debug(f"Fetching: {header}")
            val = row.get(header, None)
            row_data.append(val)
            logger.debug(f'Set to: {val}')
        output.append(row_data)
    return output


def reorder_csv(incoming):
    if incoming.get('source') is None:
        return incoming

    data = incoming.copy()

    csvbuffer = io.StringIO(data['source'].decode('UTF-8'))

    output = io.StringIO()
    headers = []
    header_mapping = {}
    writer = None
    # This will make sure empty lines are not deleted
    lines = (',' if line.isspace() else line for line in csvbuffer)

    for row in csv.DictReader(lines):
        if not headers:
            # write headers first
            headers = get_ordered_headers(list(row.keys()))
            writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            if (isinstance(ingest_settings.UPLOAD_SETTINGS['STREAM_ARGS']['headers'], list)):
                header_mapping = dict(zip(row.keys(), headers))
        # If there's extra item in the row
        if row.get(None):
            vals = [row.get(header, '') for header in headers]
            vals.extend(row.get(None))
            write_row = ",".join(vals)

            output.write(write_row + '\n')
        else:
            writer.writerow(OrderedDict([(header_mapping.get(k, k), v) for k, v in row.items()]))

    data['source'] = output.getvalue().encode('UTF-8')
    return data
