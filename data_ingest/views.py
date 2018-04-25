import io


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.module_loading import import_string
from django.urls import reverse

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Upload
from .forms import UploadForm
from . import ingest_settings

from django.http import HttpResponseRedirect

SESSION_KEY = "ingestor"


class UploadList(LoginRequiredMixin, ListView):
    model = ingest_settings.model_form_class

    def get_queryset(self):
        return Upload.objects.filter(submitter=self.request.user).order_by(
            "-created_at"
        )


@login_required
def upload(request, **kwargs):

    if request.method == "POST":

        # create a form instance and populate it with data from the request:
        form = ingest_settings.upload_form_class(request.POST, request.FILES)
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
            ingestor = ingest_settings.ingestor_class(instance)
            instance.validation_results = ingestor.validate()
            instance.save()
            request.session["upload_id"] = instance.id

            if instance.validation_results["valid"]:
                return HttpResponseRedirect("/data_ingest/review-rows/")

            else:
                return HttpResponseRedirect("/data_ingest/review-errors/")

    else:
        form = ingest_settings.upload_form_class(initial=request.GET)

    return render(request, ingest_settings.UPLOAD_SETTINGS['TEMPLATE'], {"form": form})


def review_errors(request):
    upload = Upload.objects.get(pk=request.session["upload_id"])
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    return render(request, "data_ingest/review-errors.html", data)


def confirm_upload(request):
    upload = Upload.objects.get(pk=request.session["upload_id"])
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    return render(request, "data_ingest/confirm-upload.html", data)


def complete(request):
    pass
