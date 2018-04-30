
# Defaults example app

Demonstrates the ingest module's behavior with an absolute
minimum of configuration, exposing all the defaults.

To run it locally:

1. `python manage.py migrate`

1. Create a user account: `python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('chris', 'chris@gsa.gov', 'publicservice')"`

1. `createdb default_ingestor` (Requires PostgreSQL, which supports JSON data types)

1. `python manage.py runserver`

1. Open http://localhost:8000/ingest/ in a web browser.

This app was created by

1. Running `django-admin startproject`

1. In `settings.py`, switching database engine to postgresql,
   and adding `'data_ingest'` to `INSTALLED_APPS`

1. In `urls.py`, adding 

    url(r'^data_ingest/', include(data_ingest.urls)),





