from django.apps import AppConfig
from django.core.cache import cache
from .server_classes import ServerManager

class ScalingManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scaling_manager'
    
    def ready(self):
        print("__________________________________________")
        cache.set("gameserver_manager", ServerManager())
        cache.set("thread_running", False)
        # cache.set("available_gameserver_list", ["0.0.0.0:8888", ])
        return