"""
This module has functions to perform certain AWS operations (required by our app) using boto3
"""
import boto3
import botocore
from django.conf import settings

# uncomment if running this separately (probably if MAIN)
# ecs_client = boto3.client("ecs", region_name = "ap-south-1")
# ec2_client = boto3.client("ec2", region_name = "ap-south-1")
# ec2_launch_template = 'defaultECS'

def get_address(task_arn: str) -> str:
    """ Returns the ip address of the ECS instance on which the task is running. 
    If the task is in PENDING state, it waits for it to run. 
    In case of error, it returns an empty string and prints the error on console.
    """
    # TODO: Divide into multiple functions
    ecs_client = settings.ECS_CLIENT
    ec2_client = settings.EC2_CLIENT
    task_waiter = ecs_client.get_waiter('tasks_running')
    try:
        # wait till task status = 'RUNNING'
        task_waiter.wait(
            # DEFAULT_CLUSTER
            tasks=[
                task_arn,
            ]
        )
        # Get task info
        task_description = ecs_client.describe_tasks(
            # DEFAULT_CLUSTER
            tasks=[
                task_arn,
            ]
        )['tasks'][0]
        # Extract port exposed
        network_binding = task_description['containers'][0]['networkBindings'][0]
        gs_port: str = str(network_binding['hostPort'])
        
        # Get ecs instance info
        container_instance_arn = task_description['containerInstanceArn']
        container_description = ecs_client.describe_container_instances(
            # DEFAULT_CLUSTER
            containerInstances=[
                container_instance_arn,
            ]
        )['containerInstances'][0]
        ec2_id: str = container_description['ec2InstanceId'] # Extract ec2 id 

        # Get Public IP address of the EC2 instance
        ec2_instance_description = ec2_client.describe_instances(
            InstanceIds=[
               ec2_id,
            ]
        )['Reservations'][0]['Instances'][0]
        gs_ip: str = str(ec2_instance_description['PublicIpAddress'])

        gs_address = gs_ip + ":" + gs_port
        # print(gs_address)
        return gs_address
    
    except Exception as e:
        print(e.message)
        return ""

def launch_task(task_definition: str) -> str:
    """ Inititates a task and returns the task arn """
    # TODO: Error Handling
    ecs_client = settings.ECS_CLIENT
    response = ecs_client.run_task(
        taskDefinition=task_definition,
        launchType='EC2',
        # DEFAULT_CLUSTER
        count=1
    )
    task_arn = response['tasks'][0]["taskArn"]
    return task_arn

def launch_gameserver_task() -> str:
    """ Inititates the gameserver task and returns the task arn"""
    return launch_task(settings.GAMESERVER_TASK_DEFINITION)

def get_gameserver_tasks() -> list:
    """Returns list of gameserver tasks with desired status = RUNNING"""
    ecs_client = settings.ECS_CLIENT
    task_arns = ecs_client.list_tasks(
        # DEFAULT_CLUSTER
        family=settings.GAMESERVER_TASK_DEFINITION,
        desiredStatus='RUNNING'
    )['taskArns']
    return task_arns

def stop_task(task_arn: str, reason_to_stop: str = "Not specified"):
    """Stops the given task"""
    # TODO: Error Handling
    ecs_client = settings.ECS_CLIENT
    response = ecs_client.stop_task(
        # DEFAULT_CLUSTER
        task=task_arn,
        reason=reason_to_stop
    )
    

def launch_gameserver() -> str:
    """ Runs an ECS instance, waits for it to start running and then initiates gameserver task"""
    # TODO: Error Handling
    # TODO: launch ecs instance
    # TODO: EC2 scaling
    return launch_gameserver_task()

def launch_ecs_instance():
    """Launches an ECS instance"""
    # DEFAULT_CLUSTER: Refer to user data section of https://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_container_instance.html#linux-liw-advanced-details for additional steps required to use a different cluster
    # TODO: Error Handling
    ec2_client = settings.EC2_CLIENT
    response = ec2_client.run_instances(
        MaxCount=1,
        MinCount=1,
        LaunchTemplate={
            'LaunchTemplateName': settings.ECS_INSTANCE_LAUNCH_TEMPLATE,
        }
    )
    print(response)

def terminate_ecs_instance():
    # TODO
    pass

def experimental_launch_gameserver() -> str:
    # TODO: EC2 scaling
    ecs_client = settings.ECS_CLIENT
    response = ecs_client.run_task(
        taskDefinition='LaunchGameserver',
        launchType='EC2',
        placementConstraints=[
            {
                "type": "distinctInstance"
            }
        ],
        count=1
    )
    # The distinctInstance constraint places each task in the group on a different instance. It can be specified with the following actions: CreateService, UpdateService, and RunTask
    print(response)
    """
    Output in case distinctInstance contraint not specified
    {'tasks': [], 'failures': [{'arn': 'arn:aws:ecs:ap-south-1:677002189549:container-instance/9343a2bc91034510bddcebef0a29f3d9', 'reason': 'DistinctInstance 
    placement constraint unsatisfied.'}], 'ResponseMetadata': {'RequestId': '3b00184f-cf0d-438f-9bc2-2f222a6c5af3', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '3b00184f-cf0d-438f-9bc2-2f222a6c5af3', 'content-type': 'application/x-amz-json-1.1', 'content-length': '185', 'date': 'Sat, 10 Dec 2022 
    06:36:12 GMT'}, 'RetryAttempts': 0}}
    """
    task_arn = response['tasks'][0]["taskArn"]
    return task_arn

# response = ecs_client.describe_clusters()
# print(response)