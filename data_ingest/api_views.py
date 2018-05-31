from .models import Upload
from .serializers import UploadSerializer
from . import ingest_settings, ingestors
from .parsers import CsvParser
from rest_framework.parsers import JSONParser


from rest_framework import viewsets, views, decorators, response


class UploadViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ingest_settings.upload_model_class.objects.all().order_by('created_at')
    serializer_class = UploadSerializer

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

    data = request.data
    result = ingestors.apply_validators_to(data)
    return response.Response(result)


    # to use: curl - X POST - H "Content-Type: text/csv" --data-binary @myfile.csv https://...
    # omitting --data-binary strips newlines!
