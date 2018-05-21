from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from . import ingest_settings


class UploadList(LoginRequiredMixin, ListView):
    model = ingest_settings.upload_model_class
    template_name = ingest_settings.UPLOAD_SETTINGS['LIST_TEMPLATE']

    def get_queryset(self):
        return ingest_settings.upload_model_class.objects.filter(
            submitter=self.request.user).exclude(
                status='DELETED').order_by("-created_at")


class UploadDetail(LoginRequiredMixin, DetailView):

    model = ingest_settings.upload_model_class
    template_name = ingest_settings.UPLOAD_SETTINGS['DETAIL_TEMPLATE']


@login_required
def duplicate_upload(request, old_upload_id, new_upload_id):

    old_upload = ingest_settings.upload_model_class.objects.get(
        pk=old_upload_id)
    new_upload = ingest_settings.upload_model_class.objects.get(
        pk=new_upload_id)

    data = {'old_upload': old_upload, 'new_upload': new_upload}

    return render(request, "data_ingest/duplicate_upload.html", data)


@login_required
def replace_upload(request, old_upload_id, new_upload_id):
    """Replaces an upload with another upload already in progress."""

    old_upload = ingest_settings.upload_model_class.objects.get(
        pk=old_upload_id)
    new_upload = ingest_settings.upload_model_class.objects.get(
        pk=new_upload_id)

    new_upload.replaces = old_upload
    new_upload.save()
    return validate(new_upload)


def _delete_upload(upload_id):

    upload = ingest_settings.upload_model_class.objects.get(pk=upload_id)
    upload.status = 'DELETED'
    upload.save()


@login_required
def delete_upload(request, upload_id):

    _delete_upload(upload_id)
    return redirect('index')


def validate(instance):

    ingestor = ingest_settings.ingestor_class(instance)
    instance.validation_results = ingestor.validate()
    instance.save()
    if instance.validation_results["valid"]:
        return redirect('review-rows', instance.id)
    else:
        return redirect('review-errors', instance.id)


@login_required
def upload(request, replace_upload_id=None, **kwargs):

    if request.method == "POST":

        # create a form instance and populate it with data from the request:
        form = ingest_settings.upload_form_class(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            metadata = dict(form.cleaned_data.items())
            metadata.pop("file")
            replace_upload_id = metadata.pop("replace_upload_id")
            instance = ingest_settings.upload_model_class(
                file=request.FILES["file"],
                submitter=request.user,
                file_metadata=metadata,
                raw=form.cleaned_data["file"].read(),
            )
            instance.save()
            if replace_upload_id is None:
                replace_upload = instance.duplicate_of()
                if replace_upload:
                    return redirect('duplicate-upload', replace_upload.id,
                                    instance.id)
            else:
                _delete_upload(int(replace_upload_id))

            return validate(instance)

    else:
        initial = request.GET.dict()
        initial['replace_upload_id'] = replace_upload_id
        form = ingest_settings.upload_form_class(initial=initial)

    return render(request, ingest_settings.UPLOAD_SETTINGS['TEMPLATE'],
                  {"form": form})


def review_errors(request, upload_id):
    upload = ingest_settings.upload_model_class.objects.get(pk=upload_id)
    if upload.validation_results['valid']:
        return redirect('confirm-upload', upload_id)
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    data["upload_id"] = upload_id
    return render(request, "data_ingest/review-errors.html", data)


def confirm_upload(request, upload_id):
    upload = ingest_settings.upload_model_class.objects.get(pk=upload_id)
    data = upload.validation_results["tables"][0]
    data["file_metadata"] = upload.file_metadata_as_params()
    data['upload_id'] = upload.id
    return render(request, "data_ingest/confirm-upload.html", data)


def complete_upload(request, upload_id):
    upload = ingest_settings.upload_model_class.objects.get(pk=upload_id)
    upload.status = 'STAGED'
    upload.save()
    if upload.replaces:
        upload.replaces.status = 'DELETED'
        upload.replaces.save()
    return redirect('index')


def detail(request, upload_id):
    upload = ingest_settings.upload_model_class.objects.get(pk=upload_id)
    if upload.status == 'LOADING':
        if upload.validation_results['valid']:
            return redirect('confirm-upload', upload_id)
        else:
            return redirect('review-errors', upload_id)
    else:
        return redirect('upload-detail', upload_id)


def complete(request):
    pass


def insert(request, upload_id):
    upload = ingest_settings.upload_model_class.objects.get(pk=upload_id)
    ingestor = ingest_settings.ingestor_class(upload)
    ingestor.insert()
    upload.status = 'INSERTED'
    upload.save()
    return redirect('index')
