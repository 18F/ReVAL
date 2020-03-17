# API

ReVal provides a RESTful API to manage `DATA_INGEST['MODEL']` instances. The default API routing prefix is `/api/`, as defined in [urls.py](../data_ingest/urls.py "urls.py for data_ingest"). API requests may have a content type of either `text/csv` or `application/json`, but all API responses will be in JSON.

TODO: document model statuses here

# Endpoints

Supported endpoints are:

- `GET` `/api/`: obtain a list of all uploads.
  - Returns 200.

- `GET` `/api/:id`: obtain upload data.
  - Returns 200 with upload data.
  - If `:id:` does not exist, returns 404 (not found).

- `POST` `/api`:
  - Returns 200 with validation information.

- `PUT` `/api/:id`: replace an upload and validate upload
  - Returns 200 with validation information; the previous upload is saved as `replaces`. Note that a new id is generated. TODO
  - If `:id:` does not exist, returns 404 (not found).

- `PATCH` `/api/:id`: replace an upload in-place and validate upload
  - Returns 200 with validation information; the previous upload is not saved.
  - If `:id:` does not exist, returns 404 (not found).

- `DELETE` `/api/:id`: delete an upload with the id `:id`.
  - Returns 204 (no content) on success.
  - If `:id:` does not exist, returns 404 (not found).

The API also provides some custom endpoints for managing uploads:

- `POST` `/api/:id/stage`:
  - Stages the upload information (sets status to `STAGED`)
  - Returns 204 (no content) on success.

- `POST` `/api/:id/insert`:
  - Inserts the upload information (sets status to `INSERTED`)
  - If upload is not `STAGED`, returns a 400 (bad request).
  - Returns 204 (no content) on success.

The API will also return a 400 (bad request) for any requests that the API can not parse.

The API will also return a 500 (internal server error), along with an error message, if the database cannot save the upload for any reason.

## Validate endpoint

The API also provides a stand-alone validation endpoint:

- `POST` `/api/validate`: Apply configured validator(s) to request data.
  - Does not insert data in the database.
  - Returns 200 with validation information.

# Authentication

API endpoints require a [django-rest framework token to authenticate](https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication "token to authenticate from the django-rest framework").

Each user will require a token to authenticate against the API.

One way to do this is to log in as a super user and use the Django `/admin` interface:

1. Add an user (if not already done) at `/admin/auth/user/add/`.
2. Create a new token at `/admin/authtoken/token/add/`.

This token may be retrieved by the user ([see the `Obtaining a Token` example below](#obtaining-a-token "obtaining a token below")).

# Examples

## Obtaining a Token

`POST` to `/data_ingest/api/api-token-auth` to get the token for authentication.

```bash
curl -X POST \
  -F username=<your username> \
  -F password=<your password> \
  http://localhost:8000/data_ingest/api/api-token-auth/
```

You will get a JSON response back with the token:

```json
{"token": "<Token to use for authentication>"}
```

Use this token in the header for the rest of the examples below.

## Validating JSON data

<details><summary>Curl</summary>

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <Replace with your Token here>" \
  -d @test_cases.json \
  http://localhost:8000/data_ingest/api/validate/
```

</details>

<details><summary>Python</summary>

```python
import requests
import json


url = 'http://localhost:8000/data_ingest/api/validate/'

with open('test_cases.json') as infile:
    content = json.load(infile)
resp = requests.post(url,
                     json=content,
                     headers={
                        "Authorization": "Token <token>"
                     })
resp.json()
```

</details>

## Validating CSV data

<details><summary>Curl</summary>

```bash
curl -X POST \
  -H "Content-Type: text/csv" \
  -H "Authorization: Token <token>" \
  --data-binary @test_cases.csv \
  http://localhost:8000/data_ingest/api/validate/
```

</details>

<details><summary>Python</summary>

```python
import requests


url = 'http://localhost:8000/data_ingest/api/validate/'

with open('test_cases.csv') as infile:
    content = infile.read()
resp = requests.post(url,
                     data=content,
                     headers={
                        "Content-Type": "text/csv",
                        "Authorization": "Token <token>"
                     })
resp.json()
```

</details>

## List uploads
## Get upload
## Create upload
## Replace upload
## Replace upload in-place
## Delete upload
## Stage upload
## Insert upload

# Validation

## Validation response structure

After data is posted to the `validate` endpoint, one will expect a JSON response.

### Description

The response will be a JSON object with the following items:
  - **tables** - a list of **table** JSON objects
  - **valid** - boolean to indicates whether the data is valid or not

### Definitions
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

<details><summary>Example validation response</summary>

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

</details>

## Validator error codes

Each validator provides a different set of error codes. Some of these error codes are provided by the validator based on the available checks it performs. Some validators will require the application owner to define their own set of error codes. In this case, the application owner will have to provide their own error code specification.

### GoodTables validator

The GoodTables validator comes with its own set of error codes.  See the [validation documentation](https://github.com/frictionlessdata/goodtables-py#validation). There is also a [data quality specification](https://github.com/frictionlessdata/data-quality-spec/blob/master/spec.json) that defines all the available error codes from GoodTables.

### Rowwise validator

This validator includes both a JSON Logic Validator and SQL Validator.  This type of validator requires the application owner to define an error code for each rule definition.  Check with the application owner to obtain a list of error codes.  For more details on how to create your own rules, see [documentation on customizing a rowwise validator](customize.md#with-a-rowwise-validator).

### JSON Schema validator

The JSON Schema validator comes with its own set of error codes.  The error code is the "validator" being used by the recommended [Python JSONSchema Validation](https://github.com/Julian/jsonschema). [Validation keywords](https://json-schema.org/draft-07/json-schema-validation.html#rfc.section.6) will be used as error codes.
