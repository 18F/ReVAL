
# Defaults example app

Demonstrates the ingest module's behavior with an absolute
minimum of configuration, exposing all the defaults.

Created according to the [default setup instructions](../../docs/default.md)

## To run locally

Create a PostgreSQL database named `default_ingestor`, run the inital migrations, and
create a user account.

    createdb default_ingestor
    python manage.py migrate
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(
        'chris', 'chris@gsa.gov', 'publicservice')"

Run the server.

    python manage.py runserver

Visit http://localhost:8000/data_ingest/, login as `chris/publicservice`, and try uploading
some CSVs (like the provided [example](../../examples/defaults/staff.csv)).