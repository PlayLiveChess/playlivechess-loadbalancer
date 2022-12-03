from time import sleep
from tokenize import String
from django.core.cache import cache
import requests
from .aws_utils import launch_gameserver, get_address, stop_gameserver_task, get_gameserver_tasks

class Server():
    def __init__(self, task_arn: str):
        self.task_arn: str = task_arn
        self.address: str = get_address(self.task_arn)
        # we wait for a PENDING task to transition to RUNNING before its entry
        # we don't store STOPPED servers
        self.status: str = 'RUNNING' # 'RUNNING'|'PENDING'|'STOPPED'
        self.available_capacity: int = 0
        self.ready_to_close: bool = False
        self.update_state()
        
    def update_state(self):
        """
        makes api requests to update available capacity and ready to close flag
        """
        url = "http://"+self.address+"/health/"
        state_json: dict = requests.get(url).json()
        self.ready_to_close = state_json['ready_to_close']
        self.available_capacity = state_json['available_capacity']
        pass

class ServerManager():
    
    def __init__(self):
        task_arns = get_gameserver_tasks()
        self.available_servers: list = [Server(arn) for arn in task_arns]
        self.extra_servers: list = []
        self.total_available_capacity: int = 0
        for s in self.available_servers:
            self.total_available_capacity += s.available_capacity
        self.upscale_margin: int = 100
        self.downscale_margin: int = 200

    def add_server(self):
        gs_task = launch_gameserver()
        self.available_servers.append(Server(gs_task))
        cache.set("gameserver_manager", self)
        cache.set("thread_running", False)
        return
    
    def get_available_server(self) -> Server:
        max_available_server_index = self.get_available_server_index()
        self.available_servers[max_available_server_index].available_capacity -= 1
        cache.set("gameserver_manager", self)
        return self.available_servers[max_available_server_index]
    
    def get_available_server_index(self) -> int:
        max_available_server_index = 0

        for i in range(1, len(self.available_servers)):
            server = self.available_servers[i]
            if server.available_capacity > self.available_servers[max_available_server_index].available_capacity:
                max_available_server_index = i
        
        return max_available_server_index
    
    def get_available_servers(self) -> list:
        return self.available_servers

    def server_update(self) -> None:
        print("Starting server_update")

        for s in self.available_servers:
            s.update_state()
            self.total_available_capacity += s.available_capacity
        
        for s in self.extra_servers:
            s.update_state()

        print("state updated")

        if self.total_available_capacity < self.upscale_margin:
            print("Upscale")

            if len(self.extra_servers) == 0:
                self.add_server()
            else:
                s = self.extra_servers.pop(0)
                self.total_available_capacity += s.available_capacity
                self.available_servers.append(s)
        
        elif (self.total_available_capacity > self.downscale_margin) & (len(self.available_servers)>1) :
                print("Downscale")
                s = self.available_servers.pop(self.get_available_server_index())
                self.total_available_capacity -= s.available_capacity
                self.extra_servers.append(s)

        remaining_extra_servers: list = []
        for s in self.extra_servers:
            print("Removing server")

            if s.ready_to_close:
                stop_gameserver_task(s.task_arn, "Deprovisioning")
            else:
                remaining_extra_servers.append(s)
        
        self.extra_servers = remaining_extra_servers

        cache.set("thread_running", False)
        cache.set("gameserver_manager", self)
        print("Ending server_update")
        
        return