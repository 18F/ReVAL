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

    curl -X POST -H "Content-Type: application/json" -d @test_cases.json http://localhost:8000/data_ingest/api/validate/

or, in Python,

    url = 'http://localhost:8000/data_ingest/api/validate/'
    import requests
    import json
    with open('test_cases.json') as infile:
        content = json.load(infile)
    resp = requests.post(url, json=content)
    resp.json()

### Validate CSV data

    curl -X POST -H "Content-Type: text/csv" --data-binary @test_cases.csv http://localhost:8000/data_ingest/api/validate/  
    
or, in Python,

    import requests
    url = 'http://localhost:8000/data_ingest/api/validate/'
    with open('test_cases.csv') as infile:
        content = infile.read()
    resp = requests.post(url, data=content, headers={"Content-Type": "text/csv"})
    resp.json()
