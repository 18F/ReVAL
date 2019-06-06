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
can be applied to uploads by including it in `DATA_INGEST['VALIDATORS']` in `settings.py`.

```python
    'VALIDATORS': {
        'table_schema.json': 'data_ingest.ingestors.GoodtablesValidator',
    }
```

This can be a file path relative to the Django project's root,
or the URL of a Table Schema on the web.

## With a rowwise validator 

Rowwise validators are applied individually to each row, and 
require a definition file in JSON or YAML specifying a list of rules.  
Each rule is an object with `code` and a `message`.

These rules may look like 

```json
    {
        "code": "dollars_spent <= dollars_budgeted",
        "error_code": "1A",
        "message": "spending should not exceed budget",
        "columns": ["dollars_spent", "dollars_budgeted"],
        "severity": "Warning"
    }
```

### Required fields 

- `code`: An expression in the appropriate language (such as SQL or JsonLogic)
- `message`: Text to display to submitter when a row violates this rule.

#### Messages

Messages also support the use of simple string interpolation.  Anything that is included
inside the curly brackets `{}` will be evaluated and replaced by its value.
- `{column}`: By putting the column name inside the curly brackets, this will be replaced
  with the actual value of this row's column.
- `{A op B}`: `A` is a column name or a number (integer or decimal number), `op` is an arithmetic
  operator `+`, `-`, `*` or `/`, and `B` is a column name or a number (integer or decimal number).
- `{A op B:C}`: `A op B` is the same as above, `C` is the number of decimal places to display
  after the decimal.

### Optional fields 

- `error_code`: A user-defined code for this rule
- `columns`: Names of columns to highlight when a row violates this rule.  Optional.
- `severity`: `Warning` or `Error`, defaults to `Error`.  `Warning` will not prevent 
  rows from being inserted.
 
Any extra fields will be ignored.


### With [JSON Logic](http://jsonlogic.com/) 

Create a YAML or JSON list of JSON Logic rules, as described above,
and add the file to `DATA_INGEST['VALIDATORS']`. 

```python
    'VALIDATORS': {
        'json_logic.json': 'data_ingest.ingestors.JsonlogicValidator',
    },
```

### With SQL

Create a YAML or JSON list of SQL, as described above,
and add the file to `DATA_INGEST['VALIDATORS']`. 

```python
    'VALIDATORS': {
        'sql_validators.yml': 'data_ingest.ingestors.SqlValidator',
    },
```

Each rule's code should return `true` for valid rows and `false` for invalid.

At this point, SQL Validator uses in-memory SQLite database to perform its validation.

### Inverting rule logic 

By default, the code of each rule should evaluate to `true` for a row 
to be valid.  You can reverse this by defining a new validator and making the attribute `INVERT_LOGIC = True`.  There are currently two validators that do the invert rule logic: `JsonlogicValidatorFailureConditions`, and `SqlValidatorFailureConditions`.  See code in `ingestors.py` for details.

## With a JSON Schema validator

### With a custom JSON Schema

[JSON Schema](https://json-schema.org/understanding-json-schema/index.html)
supports a variety of validations.  Any valid JSON Schema
can be applied by including it in `DATA_INGEST['VALIDATORS']` in `settings.py`.

```python
    'VALIDATORS': {
        'json_schema.json': 'data_ingest.ingestors.JsonschemaValidator',
    }
```

This can be a file path relative to the Django project's root,
or the URL of a JSON Schema on the web.

Please note that when using JSON Schema Validator, you will not be able to use other tabular and rowwise validator as they are incompatible.

# Creating a new built-in validator

All validators are inherited from a base `Validator` class, which requires to define the abstract method `validate`.  You can subclass the `Validator` class to create a new built-in validator.

`validate` will take in a raw data source, and returns a dictionary object that follows the specification of `ValidationOutput.get_output()`.  This will be used as the valid validation responses as described in the [API documentation](api.md#code-200---ok).

You can refer to the code in `ingestor.py` for more details.

## Subclassing rowwise validator

If you need to create a validator that focuses on validating within each tabular row, you can subclass the `RowwiseValidator`.  This validator requires an implementation of `evaluate` method.

`evaluate` will takes in a rule and a row of data.  It will evaluate the row (which is a dictionary of key (field name)/value (field data) pair) based on the rule.  It will return a boolean.


# Customizing data ingestion behavior

## tabulator.Stream arguments 

Data is extracted from uploaded files using 
[Frictionless Data's tabulator](https://github.com/frictionlessdata/tabulator-py/),
and any arguments in the dictionary `settings.py:DATA_INGEST['STREAM_ARGS']`
will be passed to `Stream`.  For example,

```python
    DATA_INGEST = {
        'STREAM_ARGS': {'sheet': 'Data', 'headers': [3, 4] }
    }
```

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

```python
    DATA_INGEST = {
        'FORM': 'budget_data_ingest.forms.UploadForm',
    }
```

The metadata gathered from the form will now be stored together as JSON in the `file_metadata`
field of `Upload` instances.

### Enforcing metadata uniqueness

You may want to prevent multiple copies of the same file being uploaded.
A combination of metadata fields can be specified that will be used to
enforce uniqueness.  To do so, after setting up the metadata fields (as above),

1. Create a subclass of `data_ingest.models.Upload` with the fields you want to enforce as being unique (together).  [Example](../examples/p02_budgets/budget_data_ingest.models.py)

2. In `settings.py`, set DATA_INGEST['MODEL'] to your new model subclass.

```python
    DATA_INGEST = {
        'MODEL': 'budget_data_ingest.models.Upload',
    }
```

### Metadata prefix 

You may want to distinguish metadata fields from row data when 
inserting data to its final destination.  If so, use the `METADATA_PREFIX`
setting:

```python
    DATA_INGEST = {
        'METADATA_PREFIX': '_',
    }
```

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

```python
     INGEST_SETTINGS = {
        'INGESTOR': 'yourpackage.ingestors.YourIngestor',
        'DESTINATION_FORMAT': 'yourextension',
    }   
```

There is an example of adding a custom injection destination type 
in [examples/p03_budget](examples/p03_budgets).

## To a Django model

To save uploaded rows to instances of a Django data model
(rows in an underlying relational database), set
`'DJANGO_INGEST'['DESTINATION']` in `settings.py`:

```python
    DATA_INGEST = {
        'MODEL': 'budget_data_ingest.models.Upload',
    }
```

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
