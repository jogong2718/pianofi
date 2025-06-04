import boto3
import os
from functools import lru_cache
from typing import Dict, Any

@lru_cache()
def get_environment() -> str:
    """Get current environment (development, staging, production)"""
    return os.getenv("ENVIRONMENT", "development")

@lru_cache()
def get_database_url() -> str:
    """Get database URL from Parameter Store in production, .env in development"""
    env = get_environment()
    
    if env == "development":
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Use Supabase session pooler URI
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise Exception("DATABASE_URL not found in environment")
        return db_url
    
    # Production/Staging - use AWS Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameter(
            Name=f'/pianofi/{env}/database/url',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        raise Exception(f"Failed to get database URL from Parameter Store: {e}")

@lru_cache()
def get_aws_credentials() -> Dict[str, str]:
    """Get AWS credentials from Parameter Store or environment"""
    env = get_environment()
    
    if env == "development":
        from dotenv import load_dotenv
        load_dotenv()
        return {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            "aws_region": os.getenv("AWS_REGION", ""),
            "s3_bucket": os.getenv("S3_BUCKET", "")
        }
    
    # Production - get from Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        # Get multiple parameters at once
        response = ssm.get_parameters(
            Names=[
                f'/pianofi/{env}/aws/access_key_id',
                f'/pianofi/{env}/aws/secret_access_key',
                f'/pianofi/{env}/aws/region',
                f'/pianofi/{env}/s3/bucket'
            ],
            WithDecryption=True
        )
        
        params = {param['Name'].split('/')[-1]: param['Value'] for param in response['Parameters']}
        
        return {
            "aws_access_key_id": params.get("access_key_id", ""),
            "aws_secret_access_key": params.get("secret_access_key", ""),
            "aws_region": params.get("region", ""),
            "s3_bucket": params.get("bucket", "")
        }
    except Exception as e:
        raise Exception(f"Failed to get AWS credentials from Parameter Store: {e}")

@lru_cache()
def get_cors_origins() -> list:
    """Get CORS allowed origins"""
    env = get_environment()
    
    if env == "development":
        from dotenv import load_dotenv
        load_dotenv()
        origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
        return origins.split(",")
    
    # Production - get from Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameter(Name=f'/pianofi/{env}/cors/allowed_origins')
        return response['Parameter']['Value'].split(",")
    except Exception as e:
        # Fallback to restrictive CORS in production
        return ["https://yourdomain.com"]

# Configuration class for easy access
class Config:
    DATABASE_URL = get_database_url()
    AWS_CREDENTIALS = get_aws_credentials()
    CORS_ORIGINS = get_cors_origins()
    ENVIRONMENT = get_environment()