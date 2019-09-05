API
===

Some operations are available via a RESTful API.

List uploads
------------

`GET` to `/data_ingest/api/` for a list of all uploads.

Validate
--------

`POST` to `/data_ingest/api/validate/` to apply your app's validator
to a payload.  This will not insert the rows, but will provide 
error information.

This endpoint requires a token to authenticate.  Admin should be able to log into the admin page from a web browser
at `/admin/` and under "Authentication And Authorization" -> "Users", click on "+ Add" to add a user.
After a user has been added, they can obtain the token to authenticate.

### Obtain Token
`POST` to `/data_ingest/api/api-token-auth` to get the token for authentication.
The data for the post is the `username` and `password` JSON object.
```bash
curl -X POST \
-F username=<replace with what the admin gives you> \
-F password=<replace with what the admin gives you> \
http://localhost:8000/data_ingest/api/api-token-auth/
```

You will get a JSON response back with the token:
```json
{"token": "<Token to use for authentication on validate API>"}
```

Use this token in the header as shown below.

### Validate JSON data

```bash
curl -X POST \
-H "Content-Type: application/json" \
-H "Authorization: Token <Replace with your Token here>" \
-d @test_cases.json \
http://localhost:8000/data_ingest/api/validate/
```

or, in Python,

```python
url = 'http://localhost:8000/data_ingest/api/validate/'
import requests
import json
with open('test_cases.json') as infile:
    content = json.load(infile)
resp = requests.post(url,
                     json=content,
                     headers={
                        "Authorization": "Token <Replace with Token here in the form of environment variables, not raw text in the code>"
                     })
resp.json()
```

### Validate CSV data

```bash
curl -X POST \
-H "Content-Type: text/csv" \
-H "Authorization: Token <Replace with your Token here>" \
--data-binary @test_cases.csv \
http://localhost:8000/data_ingest/api/validate/
```

or, in Python,

```python
import requests
url = 'http://localhost:8000/data_ingest/api/validate/'
with open('test_cases.csv') as infile:
    content = infile.read()
resp = requests.post(url,
                     data=content,
                     headers={
                        "Content-Type": "text/csv",
                        "Authorization": "Token <Replace with Token here in the form of environment variables, not raw text in the code>"
                     })
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
    - **headers** - a list of field names for the data (for tabular data and flat JSON data)
    - **whole_table_errors** - a list of **error** JSON objects that are related to the entire table
    - **rows** - a list of **row** JSON objects
    - **valid_row_count** - an integer indicates the number of valid rows in the data
    - **invalid_row_count** - an integer indicates the number of invalid rows in the data


  - **row** -  a JSON object that indicates the errors each row has:
    - **row_number** - a number to indicate the row (JSONSchemaValidator counts from 0, otherwise counts from 2)
    - **errors** - a list of **error** JSON objects for this row
    - **data** - a dictionary of key (field name) / value (data for that field) pairs


  - **error** - a JSON object that indicates the details of an error
    - **severity** - severity of this error, right now `Error` or `Warning`
    - **code** - error code.  See [Error Codes](#error-codes) for details
    - **message** - error message that describe what the error is
    - **fields** - a list of all the field names that are associated with this error

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
                    "fields": []
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
                            "fields": []
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
                            "fields": [
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

This includes both JSON Logic Validator and SQL Validator.  This type of validators requires the app's owner to define an error code for each rule definition.  Check with app's owner to obtain a list of error codes.  For more details on how to create your own rules, see [documentation on customizing a rowwise validator](customize.md#with-a-rowwise-validator).

###### JSON Schema Validator

JSON Schema validator comes with its own set of error codes.  The error code is the "validator" being used by the recommended [Python JSONSchema Validation](https://github.com/Julian/jsonschema).  The [validation keywords](https://json-schema.org/draft-07/json-schema-validation.html#rfc.section.6) will be used as the error code.

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