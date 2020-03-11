from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from rest_framework import decorators, response, viewsets, status
from rest_framework.parsers import JSONParser
from . import ingest_settings, ingestors
from .authentication import TokenAuthenticationWithLogging
from .parsers import CsvParser
from .permissions import IsAuthenticatedWithLogging
from .serializers import UploadSerializer

import logging


logger = logging.getLogger("ReVAL")


class UploadViewSet(viewsets.ModelViewSet):
    """
    Implements a REST API around `upload_model_class`.
    """

    queryset = ingest_settings.upload_model_class.objects.exclude(
        status="DELETED"
    ).order_by("-created_at")
    serializer_class = UploadSerializer
    parser_classes = [JSONParser, CsvParser]

    @decorators.action(detail=True, methods=["POST"])
    def stage(self, request, pk=None):
        """
        Custom API action to stage (complete the upload of) an
        `upload_model_class` instance. The most previous upload (if
        any) will be marked as deleted.
        """
        upload = self.get_object()
        upload.status = "STAGED"
        upload.save()
        if upload.replaces:
            upload.replaces.status = "DELETED"
            upload.replaces.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=True, methods=["POST"])
    def insert(self, request, pk=None):
        """
        Custom API action to insert an `upload_model_class` instance. The
        instance must already be staged.
        """
        upload = self.get_object()
        if upload.status != "STAGED":
            message = {
                "error": f"expected status 'STAGED', got status '{upload.status}'"
            }
            return response.Response(message, status=status.HTTP_400_BAD_REQUEST)
        ingestor = ingest_settings.ingestor_class(upload)
        ingestor.insert()
        upload.status = "INSERTED"
        upload.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, pk=None):
        """
        Update a pre-existing `upload_model_class`. The previous instance
        will be saved. Validation errors, if any, will be stored with
        this model and validation results will be returned.
        """
        upload = self.get_object()
        return self._process_upload_model_class(request, existing_instance=upload)

    def partial_update(self, request, pk=None):
        """
        Replace the `upload_model_class` and re-validate. The previous
        instance will not be saved.
        """
        upload = self.get_object()
        return self._process_upload_model_class(request, existing_instance=upload, replace=True)

    def create(self, request, *args, **kwargs):
        """
        Create a `upload_model_class`. Submitter id will be stored with
        this model. Validation errors, if any, will also be stored
        with this model. The object status is set to LOADING by default.
        """
        return self._process_upload_model_class(request)

    def perform_destroy(self, instance):
        """
        Overridden method. Do not actually delete the instance; instead
        set the instance status to DELETED.
        """
        instance.status = "DELETED"
        instance.save()

    # TODO test with id=foo
    def _process_upload_model_class(self, request, existing_instance=None, replace=False):
        data = request.data.copy() or {}
        data["raw"] = request.data
        # metadata: include all but the uploaded file information
        data["file_metadata"] = {
            k: v
            for k, v in request.data.items()
            if k not in ["source", "format", "headers"]
        }
        data["submitter"] = request.user.id
        data["id"] = existing_instance.id if existing_instance and replace else None

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # save the serializer result separately
        instance = None
        try:
            instance = serializer.save()
            if existing_instance and not replace:
                instance.replaces = existing_instance
                instance.save()
        except IntegrityError as error:
            message = {"error": str(error)}
            return response.Response(
                message, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            # note that we use the original request.data here, since
            # the serializer instance is augmented with other derived fields
            result = ingestors.apply_validators_to(request.data, request.content_type)
            instance.validation_results = result
            instance.save()
        except AttributeError:
            message = {"error": "unexpected input"}
            return response.Response(message, status=status.HTTP_400_BAD_REQUEST)

        return response.Response(result)


@csrf_exempt
@decorators.api_view(["POST"])
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
