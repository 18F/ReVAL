import io

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.utils.module_loading import import_string

from .models import Upload
from .forms import UploadForm

from django.http import HttpResponseRedirect

upload_form_class = import_string(settings.UPLOAD_FORM)
ingestor = import_string(settings.UPLOAD_INGESTOR)

SESSION_KEY = 'ingestor'

def index(request):
    context = {}
    return render(request, 'ingest/index.html', context)

@login_required
def my_uploads(request):
    uploads = Upload.objects.filter(submitter=request.user).order_by('created_at')
    context = {'uploads': uploads}
    return render(request, 'ingest/uploads.html', context)

@login_required
def upload(request):

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = upload_form_class(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            metadata = {k: v for (k, v) in form.cleaned_data.items() if k not in ('file', )}
            instance = Upload(file=request.FILES['file'], submitter=request.user,
                file_metadata = metadata, raw=form.cleaned_data['file'].read())
            instance.save()
            instance.extracted = ingestor.extract(instance.raw)
            instance.save()  # separate save in case tabulation fails
            validation_results = ingestor.validate(instance)
            request.session[SESSION_KEY] = {'instance_id': instance.id,
                'validation_results': validation_results}
            if validation_results['valid']:
                return HttpResponseRedirect('/ingest/review-rows/')
            else:
                return HttpResponseRedirect('/ingest/review-errors/')

    else:
        form = upload_form_class()

    return render(request, settings.UPLOAD_TEMPLATE, {'form': form})


def review_errors(request):
    upload = Upload.objects.get(pk=request.session[SESSION_KEY]['instance_id'])
    validation_results = request.session[SESSION_KEY]['validation_results']
    return render(request, 'ingest/review-errors.html', validation_results['table'])
