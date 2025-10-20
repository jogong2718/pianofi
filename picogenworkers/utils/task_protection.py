import boto3
import os
ecs = boto3.client("ecs", region_name=os.environ.get("AWS_REGION", "us-east-1"))

def enable_task_protection():
    try:
        cluster = os.environ["ECS_CLUSTER"]
        task_arn = os.environ["ECS_TASK_ARN"]
        ecs.update_task_protection(
            cluster=cluster,
            tasks=[task_arn],
            protectionEnabled=True,
            expiresInMinutes=120
        )
        print(f"Enabled protection for task {task_arn}")
    except Exception as e:
        print(f"Could not enable task protection: {e}")

def disable_task_protection():
    try:
        cluster = os.environ["ECS_CLUSTER"]
        task_arn = os.environ["ECS_TASK_ARN"]
        ecs.update_task_protection(
            cluster=cluster,
            tasks=[task_arn],
            protectionEnabled=False
        )
        print(f"Cleared protection for task {task_arn}")
    except Exception as e:
        print(f"Could not clear task protection: {e}")
