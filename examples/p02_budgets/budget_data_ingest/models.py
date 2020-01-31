from django.db import models

import data_ingest.models


class Upload(data_ingest.models.Upload):
    unique_metadata_fields = [
        'year',
        'agency',
    ]


class BudgetItem(models.Model):

    year = models.IntegerField()
    agency = models.TextField()
    data_source = models.TextField()
    category = models.TextField()
    dollars_budgeted = models.DecimalField(max_digits=14, decimal_places=2)
    dollars_spent = models.DecimalField(max_digits=14, decimal_places=2)
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
    row_number = models.IntegerField()
