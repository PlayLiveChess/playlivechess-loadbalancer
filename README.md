# playlivechess-loadbalancer

Experimental django app to learn aws sdk (aws sdk for python = boto3) and threading in django

## Functionality

* Hit the available-server api to get gameserver
* Hit the available-server-list api to get list of gameservers running
* Hit the update api to update health status of all servers and scale accordingly

## Some notes about design

* For now computing power provided by RUNNING EC2 instances in the cluster are assumed to be suffiecient to meet the demand. This may not be the case always as one EC2 instance can only handle limited number of container instances
    * We may place one task one EC2 instance and scale EC2 instances along with ECS. This will allow simple EC2 scaling. (look task placement )
* Cluster name = Gameservers

## Doubts

## Resources

* [blog on custom ECS scheduler, which looks similar to what we are doing] https://aws.amazon.com/blogs/compute/how-to-create-a-custom-scheduler-for-amazon-ecs/
* [boto3 api doc]: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task
* [boto3 tutorial for ECS] https://hands-on.cloud/working-with-ecs-in-python-using-boto3/
* [ECS clsuter auto scaling doc] https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-auto-scaling.html
* [Resource limit error on run_task] https://stackoverflow.com/questions/54466796/getting-resourcememory-error-on-a-new-cluster-in-aws-ecs
* [get public ip of gameserver] https://stackoverflow.com/questions/37728119/aws-ecs-get-public-ip-of-the-instance-container-when-start-task-is-called
* [TODO] add youtube tutorial for ECS deployment

# Ignore this branch