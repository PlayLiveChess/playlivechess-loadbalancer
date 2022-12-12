"""
This module has functions to perform certain AWS operations (required by our app) using boto3
Note: There is no exception handling done by the module functions. Exceptions must be handled by the calling functions.
"""
from django.conf import settings

# uncomment if running this separately (probably if MAIN)
# ecs_client = boto3.client("ecs", region_name = "ap-south-1")
# ec2_client = boto3.client("ec2", region_name = "ap-south-1")
# ec2_launch_template = 'defaultECS'

# all these functions throw exceptions if something is off and don't handle any unexpected paramters or api responses

def running_task_waiter(task_arn: str, ecs_client) -> None:
    """Waits for the specified task to start running"""
    task_waiter = ecs_client.get_waiter('tasks_running')
    # wait till task status = 'RUNNING'
    task_waiter.wait(
        # DEFAULT_CLUSTER
        tasks=[
            task_arn,
        ]
    )

def get_task_description(task_arn: str, ecs_client) -> dict:
    """Returns description of the specified task"""
    task_description = ecs_client.describe_tasks(
        # DEFAULT_CLUSTER
        tasks=[
            task_arn,
        ]
    )['tasks'][0]
    return task_description

def get_exposed_port(task_description: dict) -> str:
    """Extracts and returns the port exposed from task description of a running task"""
    network_binding = task_description['containers'][0]['networkBindings'][0]
    port: str = str(network_binding['hostPort'])
    return port

def get_ec2_id(task_description: dict, ecs_client) -> str:
    """Returns ec2 id of the instance on which task is running"""
    container_instance_arn = task_description['containerInstanceArn']
    container_description = ecs_client.describe_container_instances(
        # DEFAULT_CLUSTER
        containerInstances=[
            container_instance_arn,
        ]
    )['containerInstances'][0]
    ec2_id: str = container_description['ec2InstanceId'] # Extract ec2 id 
    return ec2_id

def get_ip(ec2_id: str, ec2_client) -> str:
    """Returns the Public IP address of the EC2 instance"""
    ec2_instance_description = ec2_client.describe_instances(
        InstanceIds=[
            ec2_id,
        ]
    )['Reservations'][0]['Instances'][0]
    ip: str = str(ec2_instance_description['PublicIpAddress'])
    return ip
    
def launch_task(task_definition: str) -> str:
    """ Inititates a task and returns the task arn """
    ecs_client = settings.ECS_CLIENT
    response = ecs_client.run_task(
        taskDefinition=task_definition,
        launchType='EC2',
        # DEFAULT_CLUSTER
        count=1
    )
    task_arn = response['tasks'][0]["taskArn"]
    return task_arn

def get_tasks(task_family: str) -> list:
    """Returns the list of tasks (arns) of the specified family with desired status = RUNNING"""
    ecs_client = settings.ECS_CLIENT
    task_arns = ecs_client.list_tasks(
        # DEFAULT_CLUSTER
        family=task_family,
        desiredStatus='RUNNING'
    )['taskArns']
    return task_arns

def stop_task(task_arn: str, reason_to_stop: str = "Not specified"):
    """Stops the given task"""
    ecs_client = settings.ECS_CLIENT
    response = ecs_client.stop_task(
        # DEFAULT_CLUSTER
        task=task_arn,
        reason=reason_to_stop
    )
    
def launch_ecs_instance():
    """Launches an ECS instance"""
    # DEFAULT_CLUSTER: Refer to user data section of https://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_container_instance.html#linux-liw-advanced-details for additional steps required to use a different cluster
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