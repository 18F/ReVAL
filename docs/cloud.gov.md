# Cloud.gov setup

If you would like to deploy your project to [cloud.gov](https://cloud.gov/), here's a quick installation guide.  Please note that this is an example of how you can deploy to [cloud.gov](https://cloud.gov/).  There are other ways that may fit better for your deployment pipeline.  Please refer to [cloud.gov documentation](https://cloud.gov/docs/) for other ways.

In your `<myproject>/settings.py`:

- Use the following `DATABASE`, and replace `myprojectdb` with the name of your database.

```python
import dj_database_url

DATABASES = {'default': dj_database_url.config(
    default='postgres:///myprojectdb')}
```

- Add `ALLOWED_HOST`.
```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.cloud.gov',
]
```

- Specify the `STATIC_ROOT`.

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

Generate a `requirements.txt` file from the `Pipfile.lock` in your base directory.  Run the following from the shell in your base directory.

```bash
pipenv lock -r > requirements.txt
```

Specify the version of python you are running in a `runtime.txt` file in your base directory.  In our case, we are running 3.6.
```bash
python-3.6.x
```

Create a `manifest.yml` file in your base directory.  Replace the `application-name` with the application name you would like to deploy to, and `myprojectdb` with the database name you are using.
```yml
applications:
- name: application-name
  services:
   - myprojectdb
```

Create a `run.sh` file in your base directory with the following information.  The arguments of `create_user` method is the username, email address, and password respectively.  You can make use of environment variables for each of these arguments to prevent exposing these information.  Please **do not** post these information publicly.
```bash
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('user1', 'user1@example.gov', 'password')"
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('user2', 'user2@example.gov', 'password')"
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('user3', 'user3@example.gov', 'password')"
```

Create a `Procfile` file in your base directory with the following information.  This file will run when deployed.
```bash
web: ./run.sh
```

On cloud.gov, you will need to create a service instance for your database, which will be a psql service.  For more information on how to do it, refer to [managed services documentation](https://cloud.gov/docs/apps/managed-services/).

Once everything is in place, you can push the application to cloud.gov.  You will first need to log into cloud.gov and go to your org and space.  If you ever need to re-deploy your application, you can also use this command from your base directory, and replace `application-name` with your application name in your `manifest.yml` file.  See [deployment documentation](https://cloud.gov/docs/apps/deployment/) on cloud.gov for more details.

```bash
cf push application-name
```