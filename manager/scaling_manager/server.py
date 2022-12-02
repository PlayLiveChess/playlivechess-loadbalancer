from time import sleep
from tokenize import String
from django.core.cache import cache

class ServerManager():
    
    def __init__(self) -> None:
        self.available_servers = ["0.0.0.0:8888"]
        return

    def add_server(self):
        sleep(15)
        self.available_servers.append("0.0.0.0:8889")
        cache.set("gameserver_manager", self)
        cache.set("thread_running", False)
        return
    
    def get_available_servers(self) -> list:
        return self.available_servers