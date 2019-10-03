from django.apps import AppConfig
from .signals import setup_signals


class IngestConfig(AppConfig):
    name = 'data_ingest'

    def ready(self):
        setup_signals()
