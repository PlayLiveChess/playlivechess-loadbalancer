"""This module has classes (Server and ServerManager) for management and autoscaling of Gameservers on AWS"""

from time import sleep
from django.conf import settings
import requests
from threading import Thread
from .aws_utils import launch_gameserver, get_ip, get_exposed_port, get_ec2_id, get_task_description, running_task_waiter, stop_task, get_gameserver_tasks

class Server():
    """
    Wrapper class to store relevant info about a RUNNING ECS server instance

    Attributes:
    * task_arn: string storing aws task arn of the server instance
    * address: string storing socket address of the server instance
    * status: string from {'RUNNING', 'PENDING', 'STOPPED'}
    * available_capacity: integer measure of capacity of the server instance to handle future connections; note that this is weakly consistent and not real time
    * ready_to_close: boolean flag specifying whether the server instance can be terminated
    """

    def __init__(self, task_arn: str):
        """Waits for the task to transition to RUNNING state and then retrieves and stores relevant details about it."""
        self.task_arn: str = task_arn
        running_task_waiter(task_arn, settings.ECS_CLIENT)
        self.status: str = 'RUNNING'
        
        task_description = get_task_description(task_arn, settings.ECS_CLIENT)

        self.ec2_id: str = get_ec2_id(task_description, settings.ECS_CLIENT)

        port: str = get_exposed_port(task_description)
        ip: str = get_ip(self.ec2_id, settings.EC2_CLIENT)
        self.address: str = ip + ":" + port

        self.available_capacity: int = 0
        self.ready_to_close: bool = False
        # self.update_state()
        
    def update_state(self) -> bool:
        """
        Makes api requests to update available capacity and ready to close flag.
        Note that the api call may fail even after the task is running condition as it takes sometime for django to setup
        Returns True if the api call is successful and False otherwise.
        """
        url = "http://"+self.address+"/health/"
        try: 
            state_json: dict = requests.get(url).json()
            self.ready_to_close = state_json['ready_to_close']
            self.available_capacity = state_json['available_capacity']
            return True
        except Exception as e:
            print(e)
            return False

class ServerManagerThread(Thread):
    """
    ServerManagerThread is subclass of thread. The thread routinely updates the state of each server instance and based on this information, it upscales/downscales server instances. (Check README and code for implementation details)
    
    Attributes:
    * available_servers: list of servers available for connection
    * standby_servers: list of servers kept in standby as part of downscaling; they will be terminated when the 'ready_to_close' flag is True.
    * total_available_capacity: integer sum of available capacity of all servers
    * upscale_margin: min extra capacity maintained; one server instance is provisioned if total_available_capacity < upscale_margin
    * downscale_margin: max extra capacity maintained, one server instance is deprovisioned if total_available_capacity > downscale_margin
    * thread_sleep_time: time interval (in seconds) before the thread carries out routine updates

    This is a singleton class, meaning only one instance of Health can be created during the scope of the proram.
    """
    __shared_instance = None
    
    def __init__(self):
        if self.__shared_instance == None:
            Thread.__init__(self)
            ServerManagerThread.__shared_instance = self
            self.setDaemon(True)

            task_arns: list = get_gameserver_tasks() # TODO: Error Handling 
            # TODO: Replace this with a generic call for all tasks
            self.available_servers: list = [Server(arn) for arn in task_arns]
            self.standby_servers: list = []
            self.total_available_capacity: int = 0
            for s in self.available_servers:
                self.total_available_capacity += s.available_capacity
            self.upscale_margin: int = settings.UPSCALE_MARGIN
            self.downscale_margin: int = settings.DOWNSCALE_MARGIN
            self.thread_sleep_time: int = settings.THREAD_SLEEP_TIME
        
        else:
            raise Exception("ServerManagerThread is Singleton class!")
    
    @staticmethod
    def get_instance():
        """Returns the singleton shared instance of this class"""
        if ServerManagerThread.__shared_instance == None:
            ServerManagerThread()
        
        return ServerManagerThread.__shared_instance

    def add_server(self) -> bool:
        """
        Attempts to add a new server instance
        Returns True if successful and False otheriwse
        """
        try:
            # TODO: Replace this with a generic call for all tasks
            gs_task = launch_gameserver()
            self.available_servers.append(Server(gs_task))
            return True
        except Exception as e:
            print(e)
            return False
    
    def get_available_server(self) -> Server:
        """Return Server object of an available server instance"""
        max_available_server_index = self.get_available_server_index()
        self.available_servers[max_available_server_index].available_capacity -= 1
        return self.available_servers[max_available_server_index]
    
    def get_available_server_index(self) -> int:
        """Return the index (in self.available_servers list) of an available server instance"""
        max_available_server_index = 0

        for i in range(1, len(self.available_servers)):
            server = self.available_servers[i]
            if server.available_capacity > self.available_servers[max_available_server_index].available_capacity:
                max_available_server_index = i
        
        return max_available_server_index
    
    def get_available_servers(self) -> list:
        """Returns the list of available server instances as maintained by the class object"""
        return self.available_servers

    def run(self):
        """Main function which carries out routinely maintainance and updates in the backgorund"""

        print("Starting server management thread")

        while(True):

            new_total_available_capacity = 0 # reset total available capacity
            for s in self.available_servers:
                s.update_state() # TODO: Error Handling; Make multiple attempts and then fail
                new_total_available_capacity += s.available_capacity

            self.total_available_capacity = new_total_available_capacity
            
            for s in self.standby_servers:
                s.update_state() # TODO: Error Handling; Make multiple attempts and then fail

            print("state updated")
            print("Total Available Capacity", end=': ')
            print(self.total_available_capacity)

            if self.total_available_capacity < self.upscale_margin:
                print("Upscale")

                if len(self.standby_servers) == 0:
                    # If there is no server in standby, launch new server instance
                    self.add_server()
                else:
                    # Move a standby server instance back as an available server
                    s = self.standby_servers.pop(0)
                    self.total_available_capacity += s.available_capacity
                    self.available_servers.append(s)
            
            elif (self.total_available_capacity > self.downscale_margin) & (len(self.available_servers)>1) :
                    print("Downscale")
                    # Move a server instance to standby
                    s = self.available_servers.pop(self.get_available_server_index())
                    self.total_available_capacity -= s.available_capacity
                    self.standby_servers.append(s)

            # Terminate standby servers with are ready to close keep only the remaining ones
            remaining_standby_servers: list = []
            for s in self.standby_servers:
                print("Removing extra servers")

                if s.ready_to_close:
                    stop_task(s.task_arn, "Deprovisioning")
                else:
                    remaining_standby_servers.append(s)
            
            self.standby_servers = remaining_standby_servers
            
            print("Ending server_update and sleeping")
            sleep(self.thread_sleep_time) # Wait a little before the next update
            
        return
