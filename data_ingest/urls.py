"""ingest URL Configuration """

from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.authtoken import views as authtoken_views

from . import api_views, views

router = routers.DefaultRouter()
router.register(r'', api_views.UploadViewSet)

urlpatterns = [
    url(r"^upload/(?P<replace_upload_id>\d+)?", views.upload, name="upload"),
    url(r"^review-errors/(?P<upload_id>\d+)",
        views.review_errors,
        name="review-errors"),
    url(r"^confirm-upload/(?P<upload_id>\d+)",
        views.confirm_upload,
        name="confirm-upload"),
    url(r"^duplicate-upload/(?P<old_upload_id>\d+)/(?P<new_upload_id>\d+)",
        views.duplicate_upload,
        name="duplicate-upload"),
    url(r"^replace-upload/(?P<old_upload_id>\d+)/(?P<new_upload_id>\d+)",
        views.replace_upload,
        name="replace-upload"),
    url(r"^delete-upload/(?P<upload_id>\d+)",
        views.delete_upload,
        name="delete-upload"),
    url(r"^stage-upload/(?P<upload_id>\d+)",
        views.stage_upload,
        name="stage-upload"),
    url(
        r"^upload-detail/(?P<pk>\d+)",
        views.UploadDetail.as_view(),
        name="detail",
    ),
    url(
        r"^insert/(?P<upload_id>\d+)",
        views.insert,
        name="insert",
    ),
    url(r"^api/api-token-auth", authtoken_views.obtain_auth_token),
    url(r"^api/validate", api_views.validate, name="validate"),
    url(r"^api/", include(router.urls)),
    url(
        r"^",
        views.UploadList.as_view(),
        name="index",
    ),
]
