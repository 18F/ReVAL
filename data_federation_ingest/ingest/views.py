import io

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.utils.module_loading import import_string
from django.urls import reverse

from .models import Upload
from .forms import UploadForm

from django.http import HttpResponseRedirect

upload_form_class = import_string(settings.UPLOAD_FORM)
ingestor_class = import_string(settings.UPLOAD_INGESTOR)

SESSION_KEY = "ingestor"


@login_required
def index(request):
    uploads = Upload.objects.filter(submitter=request.user).order_by(
        "created_at"
    )
    context = {"uploads": uploads}
    return render(request, "ingest/index.html", context)


@login_required
def upload(request, **kwargs):

    if request.method == "POST":

        # create a form instance and populate it with data from the request:
        form = upload_form_class(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            metadata = dict(form.cleaned_data.items())
            metadata.pop("file")
            instance = Upload(
                file=request.FILES["file"],
                submitter=request.user,
                file_metadata=metadata,
                raw=form.cleaned_data["file"].read(),
            )
            ingestor = ingestor_class(instance)
            instance.validation_results = ingestor.validate()
            instance.save()
            request.session["upload_id"] = instance.id

            if instance.validation_results["valid"]:
                return HttpResponseRedirect("/ingest/review-rows/")

            else:
                return HttpResponseRedirect("/ingest/review-errors/")

    else:
        form = upload_form_class(initial=request.GET)

    return render(request, settings.UPLOAD_TEMPLATE, {"form": form})


def review_errors(request):
    upload = Upload.objects.get(pk=request.session["upload_id"])
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    return render(request, "ingest/review-errors.html", data)


def confirm_upload(request):
    upload = Upload.objects.get(pk=request.session["upload_id"])
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    return render(request, "ingest/confirm-upload.html", data)


def complete(request):
    pass
