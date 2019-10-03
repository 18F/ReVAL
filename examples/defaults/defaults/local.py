import os
from .settings import *  # noqa


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'Just a simple secret key for test'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] "
                      "%(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        },
        'simple': {
            'format': "%(levelname)s %(message)s",
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'propagate': True,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'django.template': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
    },
}
