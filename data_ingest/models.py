import copy
import csv
import io
import os.path
from urllib.parse import urlencode

import tabulator
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import IntegrityError, models


def csv_to_dicts(raw):
    reader = csv.DictReader(
        io.StringIO(bytes(raw).decode("utf8")))  # TODO: encoding utf8?
    yield from reader


class UploadIntegrityError(IntegrityError):
    def __init__(self, *arg, duplicate_upload=None, **kwargs):
        self.duplicate_upload = duplicate_upload
        return super().__init__(self, *arg, **kwargs)


class Upload(models.Model):
    class Meta:
        abstract = True

    STATUS_CHOICES = (('LOADING', 'Loading'),
                      ('PENDING', 'Pending'),
                      ('STAGED', 'Staged'),
                      ('INSERTED', 'Inserted'), )

    submitter = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_metadata = JSONField(null=True)
    file = models.FileField()
    raw = models.BinaryField(null=True)
    validation_results = JSONField(null=True)
    status = models.CharField(max_length=10,
                              choices=STATUS_CHOICES,
                              default='LOADING', )
    status_changed_by = models.ForeignKey(User, related_name="+", null=True)
    status_changed_at = models.DateTimeField(null=True)

    unique_metadata_fields = []

    def enforce_unique_metadata_fields(self):
        # This is far less efficient than using a database unique index,
        # but we want to leave file_metadata very flexibly defined
        if self.unique_metadata_fields:
            duplicates = self.__class__.objects
            for field in self.unique_metadata_fields:
                duplicates = duplicates.filter(**{'file_metadata__' + field:
                                                  self.file_metadata[field]})
            duplicate = duplicates.first()
            if duplicate:
                raise UploadIntegrityError(
                    'File metadata duplicates existing upload ' +
                    str(duplicate.id),
                    duplicate_upload=duplicate)

    @property
    def file_type(self):
        (root, ext) = os.path.splitext(self.file.name)
        return ext.lower()[1:]

    def file_metadata_as_params(self):
        if self.file_metadata:
            return urlencode(self.file_metadata)
        else:
            return ""

    _MAX_N_DESCRIPTIVE_FIELDS = 4

    def descriptive_fields(self):
        return self.file_metadata or {'File Name': self.file.name}


class DefaultUpload(Upload):
    pass
