# Customizing data_ingest behavior

## Customizing validation

By default, data_ingest applies only the
[default GoodTables validator](https://github.com/frictionlessdata/goodtables-py)
which checks for basic problems like empty rows,
rows with more columns than the header, etc.

### With a custom Table Schema

[Table Schema](https://frictionlessdata.io/specs/table-schema/)
supports a variety of validations.  Any valid TableSchema
can be applied to uploads by including it in `DATA_INGEST['VALIDATION_SCHEMA']` in `settings.py`.

    DATA_INGEST = {
        'VALIDATION_SCHEMA': 'table_schema.json',
    }

This can be a file path relative to the Django project's root,
or the URL of a Table Schema on the web.

## Adding metadata

"Metadata" refers to fields that apply to an upload overall, rather
than to individual rows within it.  The default configuration collects
no metadata.

1. Create a subclass of `data_ingest.forms.UploadForm` with fields for the metadata you want to collect.  [Example](../examples/p02_budgets/budget_data_ingest.forms.py)

2. In `settings.py`, set DATA_INGEST['FORM'] to your new form subclass.

    DATA_INGEST = {
        'FORM': 'budget_data_ingest.forms.UploadForm',
    }

The metadata gathered from the form will now be stored together as JSON in the `file_metadata`
field of `Upload` instances.

### Enforcing metadata uniqueness

You may want to prevent multiple copies of the same file being uploaded.
A combination of metadata fields can be specified that will be used to
enforce uniqueness.  To do so, after setting up the metadata fields (as above),

1. Create a subclass of `data_ingest.models.Upload` with the fields you want to enforce as being unique (together).  [Example](../examples/p02_budgets/budget_data_ingest.models.py)

2. In `settings.py`, set DATA_INGEST['MODEL'] to your new model subclass.

    DATA_INGEST = {
        'MODEL': 'budget_data_ingest.models.Upload',
    }

## Changing injection destination

We "inject" data when we copy it from an `Upload` instance into
the data destination.  By default, each `Upload` is dumped as a
.json file in the `data_ingest/` directory under the Django
project root.

### To an alternate flat-file format

TODO

### To a Django model

To save uploaded rows to instances of a Django data model
(rows in an underlying relational database), set
`'DJANGO_INGEST'['DESTINATION']` in `settings.py`:


    DATA_INGEST = {
        'MODEL': 'budget_data_ingest.models.Upload',
    }

Of course, the target model must exist!  See this
[example module](../examples/p02_budget/models.py).
Include model fields for the metadata fields as well as
the data columns.  It's best to also include a `ForeignKey`
to the `Upload` model, to track the data flow for
troubleshooting, retrating/deleting uploads, etc.

### To a RESTful web service

TODO
