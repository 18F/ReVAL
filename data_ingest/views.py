import io

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.module_loading import import_string
from django.views.generic import DetailView, ListView, TemplateView

from . import ingest_settings
from .forms import UploadForm
from .models import UploadIntegrityError

SESSION_KEY = "ingestor"


class UploadList(LoginRequiredMixin, ListView):
    model = ingest_settings.upload_model_class
    template_name = ingest_settings.UPLOAD_SETTINGS['LIST_TEMPLATE']

    def get_queryset(self):
        return ingest_settings.upload_model_class.objects.filter(
            submitter=self.request.user).order_by("-created_at")


class UploadDetail(LoginRequiredMixin, DetailView):

    model = ingest_settings.upload_model_class
    template_name = ingest_settings.UPLOAD_SETTINGS['DETAIL_TEMPLATE']


class DuplicateUpload(TemplateView):

    template_name = 'duplicate_upload.ht'


@login_required
def duplicate_upload(request, old_upload, new_upload):
    data = {'old_upload': old_upload, 'new_upload': new_upload}
    return render(request, "data_ingest/duplicate_upload.html", data)


@login_required
def replace_upload(request, old_upload_id, new_upload_id):
    new_upload = ingest_settings.upload_model_class.objects.get(
        pk=new_upload_id)
    new_upload.status = 'STAGED'
    new_upload.save()
    old_upload = ingest_settings.upload_model_class.objects.get(
        pk=old_upload_id)
    old_upload.delete()
    return redirect('index')


@login_required
def delete_upload(request, upload_id):

    ingest_settings.upload_model_class.objects.get(pk=upload_id).delete()
    return redirect('index')


@login_required
def upload(request, reload_pk=None, **kwargs):

    if request.method == "POST":

        # create a form instance and populate it with data from the request:
        form = ingest_settings.upload_form_class(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            metadata = dict(form.cleaned_data.items())
            metadata.pop("file")
            reloading = metadata.pop('reloading')
            instance = ingest_settings.upload_model_class(
                file=request.FILES["file"],
                submitter=request.user,
                file_metadata=metadata,
                raw=form.cleaned_data["file"].read(), )
            ingestor = ingest_settings.ingestor_class(instance)
            instance.validation_results = ingestor.validate()
            try:
                instance.enforce_unique_metadata_fields()
            except UploadIntegrityError as ierr:
                if reloading:
                    ierr.duplicate_upload.delete()
                else:
                    instance.save()
                    return duplicate_upload(request,
                                            old_upload=ierr.duplicate_upload,
                                            new_upload=instance)
            instance.save()

            request.session["upload_id"] = instance.id

            if instance.validation_results["valid"]:
                return HttpResponseRedirect("/data_ingest/review-rows/"
                                            )  # or just redirect?
                # put id in here instead of in session?

            else:
                return HttpResponseRedirect("/data_ingest/review-errors/")

    else:
        form = ingest_settings.upload_form_class(initial=request.GET)

    return render(request, ingest_settings.UPLOAD_SETTINGS['TEMPLATE'],
                  {"form": form})


def review_errors(request):
    upload = ingest_settings.upload_model_class.objects.get(
        pk=request.session["upload_id"])
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    return render(request, "data_ingest/review-errors.html", data)


def confirm_upload(request):
    upload = ingest_settings.upload_model_class.objects.get(
        pk=request.session["upload_id"])
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    return render(request, "data_ingest/confirm-upload.html", data)


def complete_upload(request):
    upload = ingest_settings.upload_model_class.objects.get(
        pk=request.session["upload_id"])
    upload.status = 'STAGED'
    upload.save()
    return redirect('index')


def detail(request):
    upload = ingest_settings.upload_model_class.objects.get(
        pk=request.session["upload_id"])
    if upload.status == 'LOADING':
        if upload.validation_results['valid']:
            return redirect('confirm-upload')
        else:
            return redirect('review-errors')
    else:
        return redirect('upload-detail')


def complete(request):
    pass


def insert(request, pk):
    upload = ingest_settings.upload_model_class.objects.get(pk=pk)
    ingestor = ingest_settings.ingestor_class(upload)
    ingestor.insert()
    upload.status = 'INSERTED'
    upload.save()
    return redirect('index')
