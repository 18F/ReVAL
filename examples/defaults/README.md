
# Defaults example app

Demonstrates the ingest module's behavior with an absolute
minimum of configuration, exposing all the defaults.

Created according to the [default setup instructions](../../docs/default.md)

## To run locally

Create a PostgreSQL database named `default_ingestor`,
run the initial migrations, and create a user account.

This database is used for logging in and uploading files.  This is **not** used as the database for validation with SQL.  `SQLValidator` is currently using an in-memory SQLite database for validation.
```bash
createdb default_ingestor
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
some CSVs (like the provided [example](staff.csv)).

## To run on Cloud.gov

Please follow the [cloud.gov deployment instruction](../cloud.gov.md).
