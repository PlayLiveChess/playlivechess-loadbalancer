from time import sleep
from django.conf import settings
import requests
from threading import Thread
from .aws_utils import launch_gameserver, get_address, stop_task, get_gameserver_tasks

class Server():
    def __init__(self, task_arn: str):
        self.task_arn: str = task_arn
        self.address: str = get_address(self.task_arn)
        # we wait for a PENDING task to transition to RUNNING before its entry
        # we don't store STOPPED servers
        self.status: str = 'RUNNING' # 'RUNNING'|'PENDING'|'STOPPED'
        self.available_capacity: int = 0
        self.ready_to_close: bool = False
        # self.update_state()
        
    def update_state(self):
        """
        makes api requests to update available capacity and ready to close flag
        """
        url = "http://"+self.address+"/health/"
        state_json: dict = requests.get(url).json()
        self.ready_to_close = state_json['ready_to_close']
        self.available_capacity = state_json['available_capacity']
        pass

class ServerManagerThread(Thread):

    __shared_instance = None
    
    def __init__(self):
        if self.__shared_instance == None:
            Thread.__init__(self)
            ServerManagerThread.__shared_instance = self
            self.setDaemon(True)

            task_arns = get_gameserver_tasks()
            self.available_servers: list = [Server(arn) for arn in task_arns]
            self.extra_servers: list = []
            self.total_available_capacity: int = 0
            for s in self.available_servers:
                self.total_available_capacity += s.available_capacity
            self.upscale_margin: int = settings.UPSCALE_MARGIN
            self.downscale_margin: int = settings.DOWNSCALE_MARGIN
        
        else:
            raise Exception("ServerManagerThread is Singleton class!")
    
    @staticmethod
    def get_instance():
        if ServerManagerThread.__shared_instance == None:
            ServerManagerThread()
        
        return ServerManagerThread.__shared_instance

    def add_server(self):
        gs_task = launch_gameserver()
        self.available_servers.append(Server(gs_task))
        return
    
    def get_available_server(self) -> Server:
        max_available_server_index = self.get_available_server_index()
        self.available_servers[max_available_server_index].available_capacity -= 1
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

    def run(self):
        print("Starting server_update thread")

        while(True):

            new_total_available_capacity = 0
            for s in self.available_servers:
                s.update_state()
                new_total_available_capacity += s.available_capacity

            self.total_available_capacity = new_total_available_capacity
            
            for s in self.extra_servers:
                s.update_state()

            print("state updated")
            print("Total Available Capacity", end=': ')
            print(self.total_available_capacity)

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
                print("Removing extra servers")

                if s.ready_to_close:
                    stop_task(s.task_arn, "Deprovisioning")
                else:
                    remaining_extra_servers.append(s)
            
            self.extra_servers = remaining_extra_servers
            
            print("Ending server_update and sleeping")
            sleep(settings.SLEEP_TIME)
            
        return
