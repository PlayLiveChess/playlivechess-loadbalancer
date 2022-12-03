from time import sleep
from tokenize import String
from django.core.cache import cache
from .aws_utils import launch_gameserver, get_address, stop_gameserver_task, get_gameserver_tasks

class Server():
    def __init__(self, task_arn: str):
        self.task_arn: str = task_arn
        self.address: str = get_address(self.task_arn)
        # we wait for a PENDING task to transition to RUNNING before its entry
        # we don't store STOPPED servers
        self.status: str = 'RUNNING' # 'RUNNING'|'PENDING'|'STOPPED'
        self.available_capacity: int = 0
        self.ready_to_clost: bool = False
        self.update_state()
        
    
    def update_state(self):
        """
        TODO: make api calls to update available capacty and ready to close flag
        """
        pass

class ServerManager():
    
    def __init__(self):
        task_arns = get_gameserver_tasks()
        self.available_servers: list = [Server(arn) for arn in task_arns]
        self.extra_servers: list = []

    def add_server(self):
        gs_task = launch_gameserver()
        self.available_servers.append(Server(gs_task))
        cache.set("gameserver_manager", self)
        cache.set("thread_running", False)
        return
    
    def get_available_server(self) -> list:
        return self.available_servers[0]

    def get_available_servers(self) -> list:
        return self.available_servers