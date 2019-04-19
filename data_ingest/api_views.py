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
    # if request.content_type == 'application/json':
    #     print("*******************request.data******************")
    #     print(request.data)
    #     data = to_tabular(request.data)
    #     print("********************data*********************")
    #     print(data)
    # elif request.content_type == 'text/csv':
    #     # data = request.data
    #     data = reorder_csv(request.data)
    # else:
    #     data = request.data
    result = ingestors.apply_validators_to(request.data, request.content_type)

    return response.Response(result)


