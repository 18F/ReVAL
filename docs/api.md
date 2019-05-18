API
===

Some operations are available via a RESTful API.

List uploads
------------

`GET` to /data_ingest/api/ for a list of all uploads.

Validate
--------

`POST` to /data_ingest/api/validate/ to apply your app's validator
to a payload.  This will not insert the rows, but will provide 
error information.

### Validate JSON data

```bash
curl -X POST -H "Content-Type: application/json" -d @test_cases.json http://localhost:8000/data_ingest/api/validate/
```

or, in Python,

```python
url = 'http://localhost:8000/data_ingest/api/validate/'
import requests
import json
with open('test_cases.json') as infile:
    content = json.load(infile)
resp = requests.post(url, json=content)
resp.json()
```

### Validate CSV data

```bash
curl -X POST -H "Content-Type: text/csv" --data-binary @test_cases.csv http://localhost:8000/data_ingest/api/validate/
```

or, in Python,

```python
import requests
url = 'http://localhost:8000/data_ingest/api/validate/'
with open('test_cases.csv') as infile:
    content = infile.read()
resp = requests.post(url, data=content, headers={"Content-Type": "text/csv"})
resp.json()
```

### Responses

After data is posted to the `validate` endpoint, one will expect a JSON response.

#### Code: 200 - OK

##### Description

The response will be a JSON object with the following items:
  - **tables** - a list of **table** JSON objects
  - **valid** - boolean to indicates whether the data is valid or not

##### Definitions
  - **table** - a JSON object with the following items:
    - **headers** - a list of field names for the data
    - **whole_table_errors** - a list of **error** JSON objects that are related to the entire table
    - **rows** - a list of **row** JSON objects
    - **valid_row_count** - an integer indicates the number of valid rows in the data
    - **invalid_row_count** - an integer indicates the number of invalid rows in the data


  - **row** -  a JSON object that indicates the errors each row has:
    - **row_number** - a number to indicate the row
    - **errors** - a list of **error** JSON objects for this row
    - **data** - a dictionary of key (field name) / value (data for that field) pairs


  - **error** - a JSON object that indicates the details of an error
    - **severity** - severity of this error, right now `Error` or `Warning`
    - **code** - error code.  See [Error Codes](#error-codes) for details
    - **message** - error message that describe what the error is
    - **error_columns** - a list of all the field names that are associated with this error

##### Example Value

```json
{
    "tables": [
        {
            "headers": [
                "category",
                "dollars_budgeted",
                "dollars_spent",
                "extra"
            ],
            "whole_table_errors": [
                {
                    "severity": "Error",
                    "code": "extra-header",
                    "message": "There is an extra header in column 4",
                    "error_columns": []
                }
            ],
            "rows": [
                {
                    "row_number": 2,
                    "errors": [
                        {
                            "severity": "Error",
                            "code": "blank-row",
                            "message": "Row 2 is completely blank",
                            "error_columns": []
                        }
                    ],
                    "data": {
                        "category": "",
                        "dollars_budgeted": "",
                        "dollars_spent": "",
                        "extra": ""
                    }
                },
                {
                    "row_number": 3,
                    "errors": [],
                    "data": {
                        "category": "pencils",
                        "dollars_budgeted": "500",
                        "dollars_spent": "400",
                        "extra": "1"
                    }
                },
                {
                    "row_number": 4,
                    "errors": [
                        {
                            "severity": "Error",
                            "code": null,
                            "message": "spending should not exceed budget",
                            "error_columns": [
                                "dollars_budgeted",
                                "dollars_spent"
                            ]
                        }
                    ],
                    "data": {
                        "category": "red tape",
                        "dollars_budgeted": "2000",
                        "dollars_spent": "2300",
                        "extra": "2"
                    }
                }
            ],
            "valid_row_count": 1,
            "invalid_row_count": 2
        }
    ],
    "valid": false
}
```

##### Error Codes

Each validator will provide a different set of error codes.  Some of the codes will be provided by the validator based on the available checks it performs.  Some validators will require app's owner to define their own set of error codes.  In this case, the app's owner will provide the error code specification.

###### GoodTables Validator

GoodTables validator comes with its own set of error codes.  See the [validation](https://github.com/frictionlessdata/goodtables-py#validation) it performs where each check is an error code. Here's the [data quality specification](https://github.com/frictionlessdata/data-quality-spec/blob/master/spec.json) that defines all the available error codes from GoodTables.

###### Rowwise Validator

This includes both JSON Logic Validator and SQL Validator.  This type of validators requires the app's owner to define an error code for each rule definition.  Check with app's owner to obtain a list of error codes.  For more details on how to create your own rules definition file, see [documentation on customizing a rowwise validator](customize.md#with-a-rowwise-validator).


#### Code: 400 - Bad Request

##### Description

The response will be a JSON object to indicate the error.


##### Example Value

i.e. This is to indicate incorrect JSON format when media type is JSON.

```json
{
    "detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"
}
```