import copy
import csv
import io
import os.path
from urllib.parse import urlencode

import tabulator
import deep_merge

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
    unique_metadata_fields = models.TextField(null=True)
    file = models.FileField()
    raw = models.BinaryField(null=True)
    validation_results = JSONField(null=True)
    status = models.TextField(null=False, default='pending')
    status_changed_by = models.ForeignKey(User, related_name="+", null=True)
    status_changed_at = models.DateTimeField(null=True)

    _MAX_N_DESCRIPTIVE_FIELDS = 4

    @property
    def file_type(self):
        (root, ext) = os.path.splitext(self.file.name)
        return ext.lower()[1:]

    @property
    def all_metadata(self):
        return deep_merge.merge(self.unique_metadata, self.nonunique_metadata)

    def file_metadata_as_params(self):
        if self.file_metadata:
            return "?" + urlencode(self.all_metadata)
        else:
            return ""

    _MAX_N_DESCRIPTIVE_FIELDS = 4

    def descriptive_fields(self):
        return self.file_metadata or {'File Name': self.file.name}