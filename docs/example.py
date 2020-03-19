#!/usr/bin/env python
#
# Example script demonstrating API and upload model life-cycle.


import sys
import requests


base_url = "http://localhost:8000/data_ingest/api"

# first, obtain our token from the API.
resp = requests.post(
    f"{base_url}/api-token-auth/", data=dict(username="username", password="password"),
)

# do we have a valid token? if not, exit.
token_result = resp.json()
if "token" not in token_result:
    print(f"error: could not obtain token: {token_result}")
    sys.exit(1)
token = token_result["token"]
print(f"obtained token: {token}")

# set up headers. you may set Content-Type to "text/csv" if you are
# primarily using csv files. for this example, though, we assume json.
headers = {
    "Content-Type": "application/json",  # or "text/csv"
    "Authorization": f"Token {token}",
}

# load our test data. note that we want plain string for the request
# `data` keyword parameter, not a dictionary object.
with open("test_cases.json") as infile:  # or "test_cases.csv"
    content = infile.read()

# create a new upload object.
resp = requests.post(f"{base_url}/", data=content, headers=headers)
id = resp.json()["id"]
print(f"created a new upload with id: {id}")

# set up a new upload url so we can modify this instance directly.
upload_url = f"{base_url}/{id}"

# modify the upload object. the previous instance will be saved, and
# we will get back a new id.
resp = requests.put(f"{upload_url}/", data=content, headers=headers)
id = resp.json()["id"]
print(f"modified upload, new id is: {id}")

# modify the upload object in-place. the previous instance will not be
# saved.
resp = requests.patch(f"{upload_url}/", data=content, headers=headers)
id = resp.json()["id"]
print(f"modified upload in-place, id is: {id}")

# ...validate this upload model further...

# now that we're satisfied with validation, we may stage (mark for
# final review).
resp = requests.post(f"{upload_url}/stage/", data=content, headers=headers)
print(f"staged upload, status code was: {resp.status_code}")

# ...process this upload model further...

# everything looks great, let's insert.
resp = requests.post(f"{upload_url}/insert/", data=content, headers=headers)
print(f"inserted upload, status code was: {resp.status_code}")

# we're done with this upload, so delete it. note that this is a
# "soft" delete: the original upload will still be in the database
# with a status of "DELETED".
resp = requests.delete(f"{upload_url}/", headers=headers)
print(f"deleted upload, status code was: {resp.status_code}")
