import logging

from django.views.decorators.csrf import csrf_exempt
from rest_framework import decorators, response, viewsets
from rest_framework.parsers import JSONParser
from . import ingest_settings, ingestors
from .authentication import TokenAuthenticationWithLogging
from .parsers import CsvParser
from .permissions import IsAuthenticatedWithLogging
from .serializers import UploadSerializer


logger = logging.getLogger('ReVAL')


class UploadViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ingest_settings.upload_model_class.objects.exclude(status='DELETED').order_by('-created_at')
    serializer_class = UploadSerializer
    parser_classes = [JSONParser, CsvParser]

    def perform_destroy(self, instance):
        """
        Overridden method. Do not actually delete the instance; instead
        set the instance status to DELETED.
        """
        instance.status = 'DELETED'
        instance.save()


@csrf_exempt
@decorators.api_view(['POST'])
@decorators.parser_classes((JSONParser, CsvParser))
@decorators.authentication_classes([TokenAuthenticationWithLogging])
@decorators.permission_classes([IsAuthenticatedWithLogging])
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
    result = ingestors.apply_validators_to(request.data, request.content_type)

    return response.Response(result)
