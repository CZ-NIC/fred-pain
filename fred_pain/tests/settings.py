"""Settings for tests."""

SECRET_KEY = 'Jean-Luc Picard'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'djmoney',
    'django_pain.apps.DjangoPainConfig',
    'fred_pain.settings.FredPainConfig',
]

PAIN_PROCESSORS = []  # type: list
