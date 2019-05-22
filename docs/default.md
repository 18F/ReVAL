# Default data_ingest setup

A bare-bones Django app using `data_ingest`

An example is available at [examples/defaults](../examples/defaults.md)

## Creating the minimal project

Create a folder for your Django project name (replace `myproject` with the project name) and go into the folder:
```bash
mkdir myproject
cd myproject
```

Install `django-data-ingest`:
- Replace `<version>` with the latest tag i.e. `v0.2` or
- Replace with `master` if you would like to work with the latest development version
```bash
    pipenv install -e git+https://github.com/18F/django-data-ingest.git@<version>#egg=django-data-ingest
```

Begin your Django project as usual.  Replace `myproject` with the name of your project.  This will create your Django project in the current directory
```bash
    django-admin.py startproject myproject .
```

In `myproject/settings.py`, add `rest_framework` and `data_ingest` to `INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'data_ingest',
]
```
Also in `myproject/settings.py`, change the `DATABASE` settings to a PostgreSQL database.  Replace `myprojectdb` with the name of your database.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myprojectdb',
    }
}
```

Add the data_ingest urls and a login url to `myproject/urls.py`.

```python
from django.conf.urls import url, include
from django.contrib import admin
import data_ingest.urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^data_ingest/', include(data_ingest.urls)),
    url('accounts/', include('django.contrib.auth.urls')),
]
```

## To run locally

Create a PostgreSQL database with the name you used, run the inital migrations, and
create a user account.

```bash
createdb myprojectdb
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user(
    'chris', 'chris@gsa.gov', 'publicservice')"
```
Run the server.

```bash
python manage.py runserver
```

Visit http://localhost:8000/data_ingest/, login with the account you created, and try uploading some
CSV files.

## To run on Cloud.gov

Please follow the [cloud.gov deployment instruction](cloud.gov.md)


## Default behavior

- No metadata is added to the files.  ([To change](customize.md))
- The only validation applied is [Goodtables](http://goodtables.okfnlabs.org/)' default validator.  This simply ensures that a CSV has a fundamentally valid form.  ([To change](customize.md))
- Inserting files saves the data as JSON files in a `data_ingest/` directory under the project directory.  ([To change](customize.md))

