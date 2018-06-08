# Customizing validation

By default, data_ingest applies only the
[default GoodTables validator](https://github.com/frictionlessdata/goodtables-py)
which checks for basic problems like empty rows,
rows with more columns than the header, etc.

## Specifying `VALIDATORS`

Any number of validators can be applied by adding them to 
`DATA_INGEST['VALIDATORS']`.  The key should be the filename
(or URL of a file to be downloaded); the value should be the 
validator class used with that file.  `data_ingest` supplies
built-in validators for 
[Table Schema](https://frictionlessdata.io/specs/table-schema/),
[JsonLogic](http://jsonlogic.com/), 
and [sqlite](https://www.sqlite.org/index.html) SQL.

If the order of application is 
important, `DATA_INGEST['VALIDATORS']` can be an 
[OrderedDict](https://docs.python.org/3/library/collections.html#collections.OrderedDict).

## With a whole-table validator 

### With a custom Table Schema

[Table Schema](https://frictionlessdata.io/specs/table-schema/)
supports a variety of validations.  Any valid TableSchema
can be applied to uploads by including it in `DATA_INGEST['VALIDATION_SCHEMA']` in `settings.py`.

    'VALIDATORS': {
        'table_schema.json': 'data_ingest.ingestors.GoodtablesValidator',
    }

This can be a file path relative to the Django project's root,
or the URL of a Table Schema on the web.

## With a rowwise validator 

Rowwise validators are applied individually to each row, and 
require a definition file in JSON or YAML specifying a list of rules.  
Each rule is an object with `code` and a `message`.

These rules may look like 

    {"code": "dollars_spent <= dollars_budgeted",
     "error_code": "1A",
     "message": "spending should not exceed budget",
     "columns": ["dollars_spent", "dollars_budgeted",
     "severity": "Warning}
     
### Required fields 

- `code`: An expression in the appropriate language (such as SQL or JsonLogic)
- `message`: Text to display to submitter when a row violates this rule.

### Optional fields 

- `error_code`: A user-defined code for this rule
- `columns`: Names of columns to highlight when a row violates this rule.  Optional.
- `severity`: `Warning` or `Error`, defaults to `Error`.  `Warning` will not prevent 
  rows from being inserted.
 
Any extra fields will be ignored.


### With [JSON Logic](http://jsonlogic.com/) 

Create a YAML or JSON list of JSON Logic rules, as described above,
and add the file to `DATA_INGEST['VALIDATORS']`. 

    'VALIDATORS': {
        'json_logic.json': 'data_ingest.ingestors.JsonlogicValidator',
    },
    
### With SQL

Create a YAML or JSON list of SQL, as described above,
and add the file to `DATA_INGEST['VALIDATORS']`. 

    'VALIDATORS': {
        'sql_validators.yml': 'data_ingest.ingestors.SqlValidator',
    },

Each rule's code should return `true` for valid rows and `false` for invalid.

### Inverting rule logic 

By default, the code of each rule should evaluate to `true` for a row 
to be valid.  You can reverse this - making each rule in a given validator 
represent invalidation - in `DATA_INGEST['VALIDATORS']`:

    'VALIDATORS': {
        'sql_validators.yml': {'FILE': data_ingest.ingestors.SqlValidator',
                               'RULES_EXPRESS_SUCCESS': False}
    },

# Customizing data ingestion behavior

## tabulator.Stream arguments 

Data is extracted from uploaded files using 
[Frictionless Data's tabulator](https://github.com/frictionlessdata/tabulator-py/),
and any arguments in the dictionary `settings.py:DATA_INGEST['STREAM_ARGS']`
will be passed to `Stream`.  For example,

    DATA_INGEST = {
        'STREAM_ARGS': {'sheet': 'Data', 'headers': [3, 4] }
    }
    
would extract data from the `Data` sheet of a spreadsheet workbook, and would 
use lines 3 and 4 as column headers.

## Customizing ingestors 

If the files are in a format more irregular than 
[tabulator](https://github.com/frictionlessdata/tabulator-py) 
can handle format (like spreadsheets
where the relevant cells are not in a contiguous block), you 
can sublass `ingestors.py:Ingestor`.  

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

### Metadata prefix 

You may want to distinguish metadata fields from row data when 
inserting data to its final destination.  If so, use the `METADATA_PREFIX`
setting:

    DATA_INGEST = {
        'METADATA_PREFIX': '_',
    }
   
`METADATA_PREFIX` will also be attached to `row_number` in the inserted
data.

This can help avoid field name collisions if uploaded files have fields 
with the same name as metadata fields.

# Changing injection destination

We "inject" data when we copy it from an `Upload` instance into
the data destination.  By default, each `Upload` is dumped as a
.json file in the `data_ingest/` directory under the Django
project root.  

Change `DATA_INGEST['DESTINATION']` in settings.py 
to save it elsewhere.

## To a RESTful web service 

Set `DATA_INGEST['DESTINATION_FORMAT']` to a webservice endpoint's 
full URL, and the upload contents will be POSTed there as JSON.
 
## To a different flat-file format

Change `DATA_INGEST['DESTINATION_FORMAT']` to save the file in a 
different format.  So far `yaml`, `json`, and `csv` are supported.

To add a format not yet supported,

- Subclass `ingestors.py:Ingestor` and give it an `insert_yourformat(self)`
method modeled on `Ingestor.insert_json`

- Include `yourextension: insert_yourmodel` in your subclass' `inserters` 
attribute.

- Edit your settings to use the new ingestor subclass.


     INGEST_SETTINGS = {
        'INGESTOR': 'yourpackage.ingestors.YourIngestor',
        'DESTINATION_FORMAT': 'yourextension',
    }   
    
There is an example of adding a custom injection destination type 
in [examples/p03_budget](examples/p03_budgets).

## To a Django model

To save uploaded rows to instances of a Django data model
(rows in an underlying relational database), set
`'DJANGO_INGEST'['DESTINATION']` in `settings.py`:


    DATA_INGEST = {
        'MODEL': 'budget_data_ingest.models.Upload',
    }

Of course, the target model must exist!  See this
[example module](../examples/p02_budget/models.py).
Include model fields for the data columns, the metadata fields,
a `ForeignKey` to the `Upload` model, and a `row_number` 
field.

# Overriding headers

When using rowwise validators (SQL or JsonLogic), It's possible to validate data submitted with inconsistently named headers 
as long as they appear in a consistent order.  Specify a list of headers in 
`settings.py:DATA_INGEST['STREAM_ARGS']['headers']`, 
then specify the row number of the to-be-replaced headers in  
`settings.py:DATA_INGEST['OLD_HEADER_ROW']`.  The user-supplied 
headers will still be used in the output, but the headers from settings.py
will be used for validation rules.

There is an example of overriding headers 
in [examples/p03_budget](examples/p03_budgets).
