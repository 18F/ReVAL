import csv
import io
import os.path

import tabulator

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField

def csv_to_dicts(raw):
    reader = csv.DictReader(io.StringIO(bytes(raw).decode('utf8')))  # TODO: encoding utf8?
    yield from reader


class Upload(models.Model):

    submitter = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file_data = JSONField(null=True)
    file_metadata = JSONField(null=True)
    file_type = models.TextField(null=True)
    file = models.FileField()
    raw = models.BinaryField(null=True)
    extracted = models.BinaryField(null=True)

    STATUS_UNREVIEWED = 0
    STATUS_APPROVED = 1
    STATUS_RETIRED = 2
    STATUS_REJECTED = 3

    STATUS_CHOICES = (
        (STATUS_UNREVIEWED, 'unreviewed'),
        (STATUS_APPROVED, 'approved'),
        (STATUS_RETIRED, 'retired'),
        (STATUS_REJECTED, 'rejected'),
    )

    status = models.IntegerField(choices=STATUS_CHOICES,
                                 default=STATUS_UNREVIEWED)
    status_changed_by = models.ForeignKey(User, related_name='+', null=True)
    status_changed_at = models.DateTimeField(null=True)

    uploaded_filename = models.CharField(
        max_length=128,
        help_text=(
            'Name of the file that was uploaded, as it was called on '
            'the uploader\'s system. For display purposes only.'
        )
    )
    serialized_gleaned_data = models.TextField(
        help_text=(
            'The JSON-serialized data from the upload, including '
            'information about any rows that failed validation.'
        )
    )

    def guess_file_type(self):
        (root, ext) = os.path.splitext(self.file.name)
        return ext.lower()[1:]

    def save(self):
        if not self.file_type:
            self.file_type = self.guess_file_type()
        return super().save()

    _READERS = {'csv': csv_to_dicts}

    def as_rows(self):
        self.file_type = self.guess_file_type()
        reader = self._READERS[self.file_type]
        yield from reader(self.extracted)

    def raw_rows(self):
        stream = tabulator.Stream(io.BytesIO(self.raw), format=self.file_type)
        stream.open()
        return list(stream)




