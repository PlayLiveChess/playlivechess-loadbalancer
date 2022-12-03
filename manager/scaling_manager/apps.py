from django.apps import AppConfig
from .server_classes import ServerManagerThread
import os

class ScalingManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scaling_manager'
    
    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':
            ServerManagerThread.get_instance().start()