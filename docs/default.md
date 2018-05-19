# Default data_ingest setup

A bare-bones Django app using `data_ingest`

An example is available at [examples/defaults](../examples/defaults.md)

## Creating the minimal project

Install Django 1.11.

    pipenv install django==1.11

Begin your Django project as usual.

    django-admin.py startproject myproject

In `myproject/settings.py`, add `data_ingest'` to `INSTALLED_APPS`.

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'data_ingest',
    ]

Also in `myproject/settings.py`, change the `DATABASE` settings to a PostgreSQL database.

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'myprojectdb',
        }
    }

Or (recommended, especially if you are deploying to cloud.gov),

    import dj_database_url

    DATABASES = {'default': dj_database_url.config(
        default='postgres:///myprojectdb')}


Add the data_ingest urls and a login url to `myproject/urls.py`.

    from django.conf.urls import url, include
    from django.contrib import admin
    import data_ingest.urls

    urlpatterns = [
        url(r'^admin/', admin.site.urls),
        url(r'^data_ingest/', include(data_ingest.urls)),
        url('accounts/', include('django.contrib.auth.urls')),
    ]

Create a PostgreSQL database with the name you used, run the inital migrations, and
create a user account.

    createdb myprojectdb
    python manage.py migrate
    python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(
        'chris', 'chris@gsa.gov', 'publicservice')"

Run the server.

    python manage.py runserver

Visit http://localhost:8000/data_ingest/, login with the account you created, and try uploading some
CSV files.


## Default behavior

- No metadata is added to the files.  ([To change](customize.md))
- The only validation applied is [Goodtables](http://goodtables.okfnlabs.org/)' default validator.  This simply ensures that a CSV has a fundamentally valid form.  ([To change](customize.md))
- Inserting files saves the data as JSON files in a `data_ingest/` directory under the project directory.  ([To change](customize.md))

- ([To change](customize.md))
- ([To change](customize.md))
- ([To change](customize.md))
- ([To change](customize.md))

