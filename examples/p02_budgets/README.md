
# Budgets example app

Demonstrates `data_ingest` with some basic [customizations](../../docs/customize.md)

## Non-default features

- [Metadata](../../docs/customize.md) is collected for each file upload.

- [Uniqueness is enforced](../../docs/customize.md) for two of the metadata fields

- [A Table Schema](../../docs/customize.md) enforces rules on the uploaded data

- Data is injected [into a database table](../../docs/customize.md) instead of to JSON files

## Configuring the project

Mostly, the project was created like the [default one](../defaults/README.md), with these
exceptions:

- Created a `budget_data_ingest` project:

    python manage.py startapp budget_data_ingest

- Added [a form](budget_data_ingest/forms.py), overriding the default `UploadForm` with one that adds three fields of metadata to each file upload

- Subclassed the default `Upload` [Django model](budget_data_ingest/models.py) to specify that two of the metadata fields should be unique together (that is, the combination of the two fields must be unique)

- Added a `BudgetItem` [Django model](budget_data_ingest/models.py) to receive data inserted from the uploads

- Added a [Goodtables](https://github.com/frictionlessdata/goodtables-py) 
  validator with constraints defined in [table_schema.json](table_schema.json)
  
- Added a [JSON file](json_logic.json) 
  containing named [JsonLogic](http://jsonlogic.com/) 
  rules for additional validation.

- Added a [JSON file](sql_rules.json)
  containing named SQL rules for additional validation.

- Additions/edits to `p02_budget/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    ...
    'budget_data_ingest',
    'data_ingest',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'budget_ingestor',
    }
}

DATA_INGEST = {
    'MODEL': 'budget_data_ingest.models.Upload',
    'FORM': 'budget_data_ingest.forms.UploadForm',
    'DESTINATION': 'budget_data_ingest.models.BudgetItem',
    'VALIDATORS': {
        'table_schema.json': 'data_ingest.ingestors.GoodtablesValidator',
        'json_logic.json': 'data_ingest.ingestors.JsonlogicValidator',
        'sql_rules.json': 'data_ingest.ingestors.SqlValidator',
    },
}
```
## To run locally

Create a PostgreSQL database named `budget_ingestor`, run the inital migrations, and
create a user account.

```bash
createdb budget_ingestor
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(
    'chris', 'chris@gsa.gov', 'publicservice')"
```

Run the server.

```bash
python manage.py runserver
```

Visit http://localhost:8000/data_ingest/, login as `chris/publicservice`, and try uploading
some CSVs (like the provided [example](b01.csv)).

## To run on Cloud.gov

Please follow the [cloud.gov deployment instruction](../cloud.gov.md)
