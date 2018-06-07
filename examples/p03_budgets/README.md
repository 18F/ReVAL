
# Budgets example app

Demonstrates `data_ingest` with some more advanced [customizations](../../docs/custom.md)

## Non-default features

- Data saved as TSVs, using a custom inserter

- Uploaded files can use their own field names 

## Configuring the project

Mostly, the project was created like the [default one](default.md), with these
additions/exceptions:

- Subclass `Ingestor` in [`budget_data_ingest/ingestors.py`](budget_data_ingest/ingestors.py)
  with a custom inserter for TSVs
  
- Additions to `p03_budget/settings.py`:

DATA_INGEST = {
    'VALIDATORS': {
        # 'usda_fns.json': 'data_ingest.ingestors.GoodtablesValidator',
        'usda_sql_rules.yml': 'data_ingest.ingestors.SqlValidator',
    },
    'STREAM_ARGS': {'sheet': 'Data',  # Uses the 'Data' sheet from workbook if .xlsx
                    'headers': UPLOAD_COLUMNS, },
    'OLD_HEADER_ROW': 1,
}

DATA_INGEST = {
    'INGESTOR': 'budget_data_ingest.ingestors.Ingestor',
    'DESTINATION_FORMAT': 'tsv',
    'STREAM_ARGS': {'headers': ['category', 'dollars_budgeted', 'dollars_spent', ]},
    'VALIDATORS': {
        'rules.json': 'data_ingest.ingestors.JsonlogicValidator',
    },
    'OLD_HEADER_ROW': 1,
}

## To run locally

Create a PostgreSQL database named `budget_ingestor`, run the inital migrations, and
create a user account.

    createdb p03_budget_ingestor
    python manage.py migrate
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(
        'chris', 'chris@gsa.gov', 'publicservice')"

Run the server.

    python manage.py runserver

Visit http://localhost:8000/data_ingest/, login as `chris/publicservice`, and try uploading
some CSVs (like the provided [example](budget.csv)).
