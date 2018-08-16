"""Settings for tests."""

SECRET_KEY = 'Jean-Luc Picard'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'djmoney',
    'django_pain.apps.DjangoPainConfig',
    'fred_pain.apps.FredPainConfig',
]

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
}

PAIN_PROCESSORS = []  # type: list

FRED_PAIN_DAPHNE_URL = ''
