import os.path
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models

User = get_user_model()


class Upload(models.Model):
    """
    An abstract model intended to be subclassed by the project
    to further define the Upload object.

    Tracks state and history of the upload 
    and who has modified it at each step.

    Also can resolve duplicate file issues, 
    if `unique_metadata_fields` is defined in the project.
    """
    class Meta:
        abstract = True

    STATUS_CHOICES = (
        ('LOADING', 'Loading'),
        ('PENDING', 'Pending'),
        ('STAGED', 'Staged'),
        ('INSERTED', 'Inserted'),
        ('DELETED', 'Deleted'),
    )
    _MAX_N_DESCRIPTIVE_FIELDS = 4

    submitter = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    file_metadata = JSONField(null=True)
    file = models.FileField()
    raw = models.BinaryField(null=True)
    validation_results = JSONField(null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='LOADING',
    )
    updated_at = models.DateTimeField(auto_now=True)
    status_changed_by = models.ForeignKey(User, related_name="+", null=True)
    status_changed_at = models.DateTimeField(null=True)
    replaces = models.ForeignKey('self', null=True, related_name='replaced_by')

    unique_metadata_fields = []

    def duplicate_of(self):
        """
        We are assuming there won't be *multiple* duplicates.

        This is far less efficient than using a database unique index,
        but we want to leave file_metadata very flexibly defined.
        """
        if self.unique_metadata_fields:
            duplicates = self.__class__.objects
            for field in self.unique_metadata_fields:
                duplicates = duplicates.filter(
                    **{'file_metadata__' + field: self.file_metadata[field]})
            # Silently delete abandoned in-process duplicates
            duplicates.filter(status='LOADING').exclude(id=self.id).delete()
            return duplicates.exclude(status='DELETED').exclude(
                id=self.id).first()
        return None

    @property
    def file_type(self):
        (root, ext) = os.path.splitext(self.file.name)
        return ext.lower()[1:]

    def file_metadata_as_params(self):
        if self.file_metadata:
            return urlencode(self.file_metadata)
        else:
            return ""

    def descriptive_fields(self):
        return self.file_metadata or {'File Name': self.file.name}


class DefaultUpload(Upload):
    """
    A simple subclass of Upload to provide a default implementation
    """
    pass
