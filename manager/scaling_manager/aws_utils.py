import boto3
import botocore
import json

ecs_client = boto3.client("ecs")
ec2_client = boto3.client("ec2")

def get_address(task_arn: str):
    task_waiter = ecs_client.get_waiter('tasks_running')
    try:
        task_waiter.wait(
            cluster='Gameservers',
            tasks=[
                task_arn,
            ]
        )
        
        task_description = ecs_client.describe_tasks(
            cluster='Gameservers',
            tasks=[
                task_arn,
            ]
        )['tasks'][0]
        network_binding = task_description['containers'][0]['networkBindings'][0]
        gs_port: str = str(network_binding['hostPort'])
        
        # get ec2 instance id
        container_instance_arn = task_description['containerInstanceArn']
        container_description = ecs_client.describe_container_instances(
            cluster='Gameservers',
            containerInstances=[
                container_instance_arn,
            ]
        )['containerInstances'][0]
        ec2_id: str = container_description['ec2InstanceId']

        ec2_instance_description = ec2_client.describe_instances(
            InstanceIds=[
               ec2_id,
            ]
        )['Reservations'][0]['Instances'][0]
        gs_ip: str = str(ec2_instance_description['PublicIpAddress'])

        gs_address = gs_ip + ":" + gs_port
        print(gs_address)
    
    except botocore.exceptions.WaiterError as e:
        print(e.message)

def launch_gameserver():
    response = ecs_client.run_task(
        taskDefinition='LaunchGameserver',
        launchType='EC2',
        cluster='Gameservers',
        count=1
    )
    task_arn = response['tasks'][0]["taskArn"]
    print(task_arn)
    
def stop_gameserver_task(task_arn: str, reason_to_stop: str = "Not specified"):
        response = ecs_client.stop_task(
            cluster='Gameservers',
            task=task_arn,
            reason=reason_to_stop
        )

task_id = "f938a4be0bf74410af456d2a4c80fca1" # technically this isn't arn, it is task id; however aws sdk accepts both

stop_gameserver_task(task_id)
# launch_gameserver()
