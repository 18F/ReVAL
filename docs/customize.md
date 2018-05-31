# Customizing data_ingest behavior

## Customizing validation

By default, data_ingest applies only the
[default GoodTables validator](https://github.com/frictionlessdata/goodtables-py)
which checks for basic problems like empty rows,
rows with more columns than the header, etc.

### Specifying `VALIDATORS`

Any number of validators can be applied by adding them to 
`DATA_INGEST['VALIDATORS']`.  The key should be the filename
(or URL of a file to be downloaded); the value should be the 
validator class used with that file.  `data_ingest` supplies
built-in validators for 
[Table Schema](https://frictionlessdata.io/specs/table-schema/) 
and [JsonLogic](http://jsonlogic.com/).

If the order of application is 
important, `DATA_INGEST['VALIDATORS']` can be an 
[OrderedDict](https://docs.python.org/3/library/collections.html#collections.OrderedDict).

### With a custom Table Schema

[Table Schema](https://frictionlessdata.io/specs/table-schema/)
supports a variety of validations.  Any valid TableSchema
can be applied to uploads by including it in `DATA_INGEST['VALIDATION_SCHEMA']` in `settings.py`.

    'VALIDATORS': {
        'table_schema.json': 'data_ingest.ingestors.GoodtablesValidator',
    }

This can be a file path relative to the Django project's root,
or the URL of a Table Schema on the web.

### With [JSON Logic](http://jsonlogic.com/)

Create a JSON file with a dictionary of rules in the form: 

    {'Descriptive rule text': {<rule in JSON Logic format>},
     ...
    }
    
Rules should return `true` for valid rows and `false` for invalid.


A sample rule file might look like

    { "spending should not exceed budget":
      {"<=" : [ { "var" : "dollars_spent" }, {"var": "dollars_budgeted"} ]},
      "spending should be between 1000 and 5000 dollars":
      {"<=" : [ 1000, { "var" : "dollars_spent" }, 5000 ]}
    }


Then add the JSON Logic rule file to `DATA_INGEST['VALIDATORS']`. 

    'VALIDATORS': {
        'json_logic.json': 'data_ingest.ingestors.JsonlogicValidator',
    },
    
### With SQL

Create a JSON or YAML file with a dictionary of rules in the form: 

    - code: field1 <= field2 
      columns: [field1, field2]
      message: field1 must not exceed field2.
        That would be bad and you should not do it.
      severity: Error

- `code`: A valid boolean SQL expression referring to field names in the data.
- `columns`: Names of columns to highlight when a row violates this rule.  Optional.
- `message`: Text to display to submitter when a row violates this rule.
- `severity`: `Warning` or `Error`, defaults to `Error`.  `Warning` will not prevent 
  rows from being inserted.
 
Any extra fields will be ignored.

Each rule's code should return `true` for valid rows and `false` for invalid.

Then add the SQL rule file to `DATA_INGEST['VALIDATORS']`. 

    'VALIDATORS': {
        'sql_rules.yml': 'data_ingest.ingestors.SqlValidator',
    },
 
### tabulator.Stream arguments 

Data is extracted from uploaded files using 
[Frictionless Data's tabulator](https://github.com/frictionlessdata/tabulator-py/),
and any arguments in the dictionary `settings.py:DATA_INGEST['STREAM_ARGS']`
will be passed to `Stream`.  For example,

    DATA_INGEST = {
        'STREAM_ARGS': {'sheet': 'Data', 'headers': [3, 4] }
    }
    
would extract data from the `Data` sheet of a spreadsheet workbook, and would 
use lines 3 and 4 as column headers.

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

## Customizing ingestors 

If the files are in an irregular format (like spreadsheets
where the relevant cells are not in a contiguous block), you 
may need to write your own ingestor.

TODO
