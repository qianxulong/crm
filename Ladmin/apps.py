from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

class LadminConfig(AppConfig):
    name = 'Ladmin'

    def ready(self):
        autodiscover_modules('Ladmin')
