import boto3
import os
import requests
import logging

ecs = boto3.client("ecs", region_name=os.environ.get("AWS_REGION", "us-east-1"))

def get_task_metadata():
    """Fetch ECS task metadata from container metadata endpoint."""
    metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
    if not metadata_uri:
        raise Exception("ECS_CONTAINER_METADATA_URI_V4 not found. Not running in ECS?")
    
    response = requests.get(f"{metadata_uri}/task", timeout=2)
    response.raise_for_status()
    metadata = response.json()
    
    # Example response structure:
    # {
    #   "Cluster": "arn:aws:ecs:us-east-1:960370336558:cluster/pianofi-cluster",
    #   "TaskARN": "arn:aws:ecs:us-east-1:960370336558:task/pianofi-cluster/abc123...",
    #   "Family": "pianofi-basicpitchworkers",
    #   ...
    # }

    logging.info(f"Fetched task metadata: {metadata}")
    
    return metadata

def enable_task_protection(local=False):
    if local:
        print("Local environment detected; skipping task protection.")
        return
    try:
        metadata = get_task_metadata()
        cluster = metadata["Cluster"]
        task_arn = metadata["TaskARN"]
        
        ecs.update_task_protection(
            cluster=cluster,
            tasks=[task_arn],
            protectionEnabled=True,
            expiresInMinutes=120
        )
        logging.info(f"Enabled protection for task {task_arn} and cluster {cluster}")
    except Exception as e:
        logging.error(f"Could not enable task protection: {e}")
        raise

def disable_task_protection(local=False):
    if local:
        logging.info("Local environment detected; skipping task protection.")
        return
    try:
        metadata = get_task_metadata()
        cluster = metadata["Cluster"]
        task_arn = metadata["TaskARN"]
        
        ecs.update_task_protection(
            cluster=cluster,
            tasks=[task_arn],
            protectionEnabled=False
        )
        logging.info(f"Cleared protection for task {task_arn}")
    except Exception as e:
        logging.error(f"Could not clear task protection: {e}")
        raise
