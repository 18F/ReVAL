import csv
import io
import os.path
from urllib.parse import urlencode

import tabulator

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField


def csv_to_dicts(raw):
    reader = csv.DictReader(
        io.StringIO(bytes(raw).decode("utf8"))
    )  # TODO: encoding utf8?
    yield from reader


class Upload(models.Model):

    submitter = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_metadata = JSONField(null=True)
    file = models.FileField()
    raw = models.BinaryField(null=True)
    validation_results = JSONField(null=True)

    STATUS_UNREVIEWED = 0
    STATUS_APPROVED = 1
    STATUS_RETIRED = 2
    STATUS_REJECTED = 3

    STATUS_CHOICES = (
        (STATUS_UNREVIEWED, "unreviewed"),
        (STATUS_APPROVED, "approved"),
        (STATUS_RETIRED, "retired"),
        (STATUS_REJECTED, "rejected"),
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_UNREVIEWED
    )
    status_changed_by = models.ForeignKey(User, related_name="+", null=True)
    status_changed_at = models.DateTimeField(null=True)

    validation_results = JSONField(null=True)

    @property
    def file_type(self):
        (root, ext) = os.path.splitext(self.file.name)
        return ext.lower()[1:]

    def file_metadata_as_params(self):
        if self.file_metadata:
            return "?" + urlencode(self.file_metadata)

        else:
            return ""
