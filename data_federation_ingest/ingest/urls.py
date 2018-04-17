"""ingest URL Configuration """

from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^upload/', views.upload, name='upload'),
    url(r'^review-errors/', views.review_errors, name='review-errors'),
    url(r'^', views.index, name='index'),
]
