
# Budgets example app

Demonstrates `data_ingest` with some more advanced [customizations](../../docs/customize.md)

## Non-default features

- Data saved as TSVs, using a custom inserter

- Uploaded files can use their own field names 

## Configuring the project

Mostly, the project was created like the [default one](../defaults/README.md), with these
additions/exceptions:

- Subclass `Ingestor` in [`budget_data_ingest/ingestors.py`](budget_data_ingest/ingestors.py)
  with a custom inserter for TSVs
  
- Additions to `p03_budget/settings.py`:

```python
DATA_INGEST = {
    'INGESTOR': 'budget_data_ingest.ingestors.Ingestor',
    'DESTINATION_FORMAT': 'tsv',
    'STREAM_ARGS': {'headers': ['category', 'dollars_budgeted', 'dollars_spent', ]},
    'VALIDATORS': {
        'rules.json': 'data_ingest.ingestors.JsonlogicValidator',
    },
    'OLD_HEADER_ROW': 1,
}
```

## To run locally

Create a PostgreSQL database named `budget_ingestor`, run the inital migrations, and
create a user account.

```bash
    createdb p03_budget_ingestor
    python manage.py migrate
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(
        'chris', 'chris@gsa.gov', 'publicservice')"
```

To create an administrator that can add users and control permissions, you can add the following superuser that can log into `/admin`.  You can replace the `username`, email address, and `password` with what you want accordingly:
```bash
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser(
        'username', 'admin@admin.com', 'password')"
```

Run the server.

```bash
    python manage.py runserver
```

Visit http://localhost:8000/data_ingest/, login as `chris/publicservice`, and try uploading
some CSVs (like the provided [example](budget.csv)).

## To run on Cloud.gov

Please follow the [cloud.gov deployment instruction](../cloud.gov.md).
