# playlivechess-manager

Django app (henceforth referred to as manager app) to manage gameservers running on AWS ECS.

## Functionality

* Provides the socket address of available gameserver instances via GET api
* Maintains the status of gameservers and performs autoscaling as per the requirement in the background

### API

* Hit the "available-server/" api to get gameserver
* Hit the "available-server-list/" api to get list of gameservers running
<!--- TODO: add response json format/example -->

## Notes

### Terms

* boto3: aws sdk for python

### Design

* Autoscaling Logic:
    * The instance of ServerManagerThread (a singleton class) handles the server management and autoscaling.
    * It stores a list of all active service instances.
        * Upon a client request, it returns the address of a server from this list to which the client can connect
        * Each service instance provides api to query available capacity and a flag (ready_to_close) to signal if it can be terminated
    * A thread keeps running in the background and carries out routinely updates and maintainance.
    * In these updates it checks the state/health of each running service instance using the api it provides.
    * Then it aggreagtes the updates to calculate total available capacity.
        * Upscale and downscale margins are given as environment variable while launching the manager app
        * If the total available capacity is less than the upscale margin, then a new instance is launched
        * If the total available capacity is more than the downscale margin, then one of the existing instances is kept in standby. We cannot directly terminate it as it may still have some active connections.
        * If standby servers are ready to close, we terminate them.
    
    * The regular server updates facillitates auto-scaling (elasticity) as well as recovery in case of failure (fault tolerance)
    * On startup, the manager app contructs its initial state by querying the relevant AWS ECS cluster for running server instances. Consequently, if the manager app fails, we just need to re-launch the app and it will recover state (Fault tolerance). 

* Current implemetation is not thread safe. Run the manager app as a single thread only (preferably using `./manage.py runserver`)
* For the sake of simplicity, it is assumed that no one interferes with the ECS resources other than the manager app while its running. Nonetheless, it can be modified to sync state with AWS resource if needed. We don't so this currently as it will severely impact the performance and complexity of the app.
* For now computing power provided by RUNNING EC2 instances in the cluster are assumed to be suffiecient to meet the demand. This may not be the case always as one EC2 instance can only handle limited number of container instances. To overcome this issue, we will place one task one EC2 instance and scale EC2 instances along with ECS. This will allow simple EC2 scaling. (look for `distinctInstance` task placement contraint in [docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-placement-constraints.html)). Relevant sections commented with `TODO: EC2 scaling`
    * If we follow this we need to handle the case where EC2 instances are already available ?
* Default cluster of AWS ECS is used for now. AWS API calls where cluster needs to specified are marked with the comment `DEFAULT_CLUSTER`.
* Error/Handling is skipped in a lot of places. These places are marked with the comment `TODO: Error Handling`
* In case, the app is unable to fetch an available gameserver, it provides the address of a backup gameserver. This can even be used for testing gameserver hosted on localhost

## Doubts

## Resources

* [blog on custom ECS scheduler, which looks similar to what we are doing] https://aws.amazon.com/blogs/compute/how-to-create-a-custom-scheduler-for-amazon-ecs/
* [boto3 api doc]: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task/
* [boto3 tutorial for ECS] https://hands-on.cloud/working-with-ecs-in-python-using-boto3/
* [ECS clsuter auto scaling doc] https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-auto-scaling.html
* [Resource limit error on run_task] https://stackoverflow.com/questions/54466796/getting-resourcememory-error-on-a-new-cluster-in-aws-ecs
* [get public ip of gameserver] https://stackoverflow.com/questions/37728119/aws-ecs-get-public-ip-of-the-instance-container-when-start-task-is-called
* [Youtube tutorial for Deployment on ECS](https://www.youtube.com/watch?v=zs3tyVgiBQQ&t=350s)

## Setup

* Provide aws permissions to the system
    * In local environment, create a `credentials` file in `~/.aws` directory, with contents as shown below
        ```
        [default]
        aws_access_key_id = Your aws access key
        aws_secret_access_key = Your aws Secret key
        ```

    * When deploying on ECS/EC2, you may place the credential file in a similar manner, or give appropriate ecsInstanceRole, the relevant permissions to access launch, describe ECS and EC2 
    instances, tasks, task definitions, clusters, etc via the AWS IAM console.
    <!--- TODO: add details and example json -->

### Environment variables
* File name: `.env`
* File location: Base directory (same level as manage.py)
```
AWS_REGION=ap_south_1
SECRET_KEY=lol
DEBUG=False
UPSCALE_MARGIN=4
DOWNSCALE_MARGIN=18
GAMESERVER_CAPACITY=10
AWS_REGION=ap-south-1
ECS_INSTANCE_LAUNCH_TEMPLATE=defaultECS
GAMESERVER_TASK_DEFINITION=LaunchGameserver
SLEEP_TIME=10
BACKUP_GAMESERVER=127.0.0.1:8888
```
### Commands to run
* Ensure the default cluster has enough capacity (EC2 instances)
* `pip install -r requirements.txt`
* `python .\manager\manage.py runserver`