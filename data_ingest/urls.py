"""ingest URL Configuration """

from django.conf.urls import include, url
from django.contrib import admin

from . import ingest_settings, views

urlpatterns = [
    url(r"^upload/((?P<reload_pk>\d+)/)?",
        views.upload,
        name="upload"),
    url(r"^review-errors/",
        views.review_errors,
        name="review-errors"),
    url(r"^confirm-upload/",
        views.confirm_upload,
        name="confirm-upload"),
    url(r"^duplicate-upload/(?P<old_upload_id>\d+)/(?P<new_upload_id>\d+)/",
        views.duplicate_upload,
        name="duplicate-upload"),
    url(r"^replace-upload/(?P<old_upload_id>\d+)/(?P<new_upload_id>\d+)/",
        views.replace_upload,
        name="replace-upload"),
    url(r"^delete-upload/(?P<upload_id>\d+)/",
        views.delete_upload,
        name="delete-upload"),
    url(r"^complete/",
        views.complete_upload,
        name="complete"),
    url(r"^upload-detail/(?P<pk>\d+)/",
        views.UploadDetail.as_view(),
        name="detail", ),
    url(r"^insert/(?P<pk>\d+)/",
        views.insert,
        name="insert", ),
    # url(r"^upload-detail/(?P<pk>\d+)/", views.UploadDetail.as_view(template_name = ingest_settings.UPLOAD_SETTINGS['DETAIL_TEMPLATE']), name="detail", ),
    url(r"^",
        views.UploadList.as_view(),
        name="index", ),
    # url(r"^", views.UploadList.as_view(template_name = ingest_settings.UPLOAD_SETTINGS['LIST_TEMPLATE']), name="index", ),
]
