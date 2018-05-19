dropdb budget_ingestor
createdb budget_ingestor
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_user('chris', 'chris@gsa.gov', 'publicservice')"
