# API

ReVal provides a RESTful API to manage `DATA_INGEST['MODEL']` instances. The default API routing prefix is `/api/`, as defined in [urls.py](../data_ingest/urls.py "urls.py for data_ingest"). API requests may have a content type of either `text/csv` or `application/json`, but all API responses will be in JSON.

The default upload model has the following statuses:

- `LOADING`: initial insert of upload data in the database.

- `PENDING`: not used at present.

- `STAGED`: stage upload data for final review.

- `INSERTED`: finalize upload data and associated validation results.

- `DELETED`: indicates a deleted upload: a "soft" delete.

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

The API will also return a 500 (internal server error), along with an error message, if the database cannot save the upload data for any reason.

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

These examples assume the default example project (included in this repository) is running on port 8000, and as such the default url is `http://localhost:8000/data_ingest`. Please adjust the url accordingly for your project.

## Obtaining a Token

You may `POST` to `/api/api-token-auth` to get your user token for authentication.

<details><summary>Example</summary>

```bash
curl -s -X POST \
  -F username=your_username_here \
  -F password=your_password_here \
  http://localhost:8000/data_ingest/api/api-token-auth/
```

```json
{"token":"faketoken"}
```

We will use this fake token in the header for the rest of the examples below. If following along, be sure to replace this fake token with your own token!

</details>

## Example data

We provide some sample runs which use the `curl` command line tool. Some of these runs use the following (deliberately incorrect) data examples:

<details><summary>Example (CSV): test_cases.csv</summary>

```csv
"Name","Title","level"
"Guido","BDFL",20

"Catherine",,9,"DBA"
,
"Tony","Engineer",10
```

</details>

<details><summary>Example (JSON): test_cases.json</summary>

```json
{
  "source": [
    {
      "Name": "Guido",
      "Title": "BDFL",
      "level": "20"
    },
    {},
    {
      "Name": "Catherine",
      "extra": "information",
      "level": 9,
      "Title": "DBA"
    },
    {
      "Name": "Tony",
      "Title": "Engineer",
      "level": "10"
    }
  ]
}
```

</details>

## List uploads

<details><summary>Example</summary>

```bash
curl -s -X GET \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/
```

```json
TODO
```

</details>

## Get upload

<details><summary>Example</summary>

```bash
curl -s -X GET \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/1
```

```json
TODO
```

</details>

## Create upload

<details><summary>Example (JSON)</summary>

```bash
curl -s -X POST \
  -d @test_cases.json \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/
```

```json
TODO
```

</details>

<details><summary>Example (CSV)</summary>

```bash
curl -s -X POST \
  -d @test_cases.json \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/
```

```json
TODO
```

</details>

## Replace upload

<details><summary>Example (JSON)</summary>

```bash
curl -s -X PUT \
  -d @test_cases.json \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/1/
```

```json
TODO
```

</details>

<details><summary>Example (CSV)</summary>

```bash
curl -s -X PUT \
  --data-binary @test_cases.csv \
  -H "Content-Type: text/csv" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/1/
```

```json
TODO
```

</details>

## Replace upload in-place

<details><summary>Example (JSON)</summary>

```bash
curl -s -X PATCH \
  -d @test_cases.json \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/1/
```

```json
TODO
```

</details>

<details><summary>Example (CSV)</summary>

```bash
curl -s -X PATCH \
  --data-binary @test_cases.csv \
  -H "Content-Type: text/csv" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/1/
```

```json
TODO
```

</details>

## Delete upload

<details><summary>Example</summary>

```bash
curl -s -X DELETE \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/4
```

```json
```

Note: on success, a 204 (no content) response code is returned.

</details>

## Stage upload

<details><summary>Example</summary>

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/5/stage/
```

```json
```

Note: on success, a 204 (no content) response code is returned.

</details>

## Insert upload

<details><summary>Example</summary>

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  http://localhost:8000/data_ingest/api/6/insert/
```

```json
```

Note: on success, a 204 (no content) response code is returned.

</details>

## Validating

<details><summary>Example (JSON)</summary>

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token faketoken" \
  -d @test_cases.json \
  http://localhost:8000/data_ingest/api/validate/
```

```json
{
  "tables": [
    {
      "headers": [
        "extra",
        "level",
        "Title",
        "Name"
      ],
      "whole_table_errors": [],
      "rows": [
        {
          "row_number": 2,
          "errors": [
            {
              "severity": "Error",
              "code": "missing-value",
              "message": "Row 2 has a missing value in column 1 (extra)",
              "fields": [
                "extra"
              ]
            }
          ],
          "data": {
            "extra": null,
            "level": "20",
            "Title": "BDFL",
            "Name": "Guido"
          }
        },
        {
          "row_number": 3,
          "errors": [
            {
              "severity": "Error",
              "code": "blank-row",
              "message": "Row 3 is completely blank",
              "fields": []
            }
          ],
          "data": {
            "extra": null,
            "level": null,
            "Title": null,
            "Name": null
          }
        },
        {
          "row_number": 4,
          "errors": [],
          "data": {
            "extra": "information",
            "level": 9,
            "Title": "DBA",
            "Name": "Catherine"
          }
        },
        {
          "row_number": 5,
          "errors": [
            {
              "severity": "Error",
              "code": "missing-value",
              "message": "Row 5 has a missing value in column 1 (extra)",
              "fields": [
                "extra"
              ]
            }
          ],
          "data": {
            "extra": null,
            "level": "10",
            "Title": "Engineer",
            "Name": "Tony"
          }
        }
      ],
      "valid_row_count": 1,
      "invalid_row_count": 3
    }
  ],
  "valid": false
}

```

</details>

<details><summary>Example (CSV)</summary>

```bash
curl -X POST \
  -H "Content-Type: text/csv" \
  -H "Authorization: Token faketoken" \
  --data-binary @test_cases.csv \
  http://localhost:8000/data_ingest/api/validate/
```

```json
{
  "tables": [
    {
      "headers": [
        "Name",
        "Title",
        "level"
      ],
      "whole_table_errors": [],
      "rows": [
        {
          "row_number": 2,
          "errors": [],
          "data": {
            "Name": "Guido",
            "Title": "BDFL",
            "level": "20"
          }
        },
        {
          "row_number": 3,
          "errors": [
            {
              "severity": "Error",
              "code": "blank-row",
              "message": "Row 3 is completely blank",
              "fields": []
            }
          ],
          "data": {
            "Name": "",
            "Title": "",
            "level": ""
          }
        },
        {
          "row_number": 4,
          "errors": [
            {
              "severity": "Error",
              "code": "extra-value",
              "message": "Row 4 has an extra value in column 4",
              "fields": []
            }
          ],
          "data": {
            "Name": "Catherine",
            "Title": "",
            "level": "9"
          }
        },
        {
          "row_number": 5,
          "errors": [
            {
              "severity": "Error",
              "code": "blank-row",
              "message": "Row 5 is completely blank",
              "fields": []
            }
          ],
          "data": {
            "Name": "",
            "Title": "",
            "level": ""
          }
        },
        {
          "row_number": 6,
          "errors": [],
          "data": {
            "Name": "Tony",
            "Title": "Engineer",
            "level": "10"
          }
        }
      ],
      "valid_row_count": 2,
      "invalid_row_count": 3
    }
  ],
  "valid": false
}
```

</details>

## Python

We provide a sample python example, which uses the [`requests` library](https://requests.readthedocs.io/en/master/ "requests library").

<details><summary>API</summary>

TODO run examples

```python
import requests


url = "http://localhost:8000/data_ingest/api/"

with open("test_cases.json") as infile:  # or "test_cases.csv"
    content = infile.read()
resp = requests.post(url,
                     data=content,
                     headers={
                        "Content-Type": "application/json",  # or "text/csv"
                        "Authorization": "Token <token>"
                     })
resp.json()
```

</details>

<details><summary>Validate</summary>

```python
import requests
import json


url = "http://localhost:8000/data_ingest/api/validate/"

with open("test_cases.json") as infile:  # or "test_cases.csv"
    content = json.load(infile)
resp = requests.post(url,
                     json=content,
                     headers={
                        "Content-Type": "application/json",  # or "text/csv"
                        "Authorization": "Token <token>"
                     })
resp.json()
```

</details>

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
