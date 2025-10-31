import boto3
import os
from functools import lru_cache
from typing import Dict, Any

@lru_cache()
def get_environment() -> str:
    """Get current environment (development, staging, production)"""
    return os.getenv("ENVIRONMENT", "production")

@lru_cache()
def get_storage() -> str:
    """Get storage type (local, s3)"""
    return os.getenv("USE_LOCAL_STORAGE", "false")

@lru_cache()
def get_database_url() -> str:
    """Get database URL from Parameter Store"""
    
    # Production/Staging - use AWS Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameter(
            Name=f'/pianofi/database/url',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        raise Exception(f"Failed to get database URL from Parameter Store: {e}")

@lru_cache()
def get_aws_credentials() -> Dict[str, str]:
    """Get AWS credentials from Parameter Store"""
    
    # Production - get from Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        # Get multiple parameters at once
        response = ssm.get_parameters(
            Names=[
                f'/pianofi/aws/region',
                f'/pianofi/s3/bucket'
            ],
            WithDecryption=True
        )
        
        params = {param['Name'].split('/')[-1]: param['Value'] for param in response['Parameters']}
        
        return {
            "aws_region": params.get("region", ""),
            "s3_bucket": params.get("bucket", "")
        }
    except Exception as e:
        raise Exception(f"Failed to get AWS credentials from Parameter Store: {e}")

@lru_cache()
def get_cors_origins() -> list:
    """Get CORS allowed origins"""
    
    # get from Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameter(Name=f'/pianofi/cors/allowed_origins')
        return response['Parameter']['Value'].split(",")
    except Exception as e:
        # Fallback to restrictive CORS in production
        return ["https://www.pianofi.ca"]
    
@lru_cache()
def get_redis_url() -> str:
    """Get Redis URL from Parameter Store"""
    
    # use AWS Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameter(
            Name=f'/pianofi/redis/url',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        raise Exception(f"Failed to get Redis URL from Parameter Store: {e}")
    
@lru_cache()
def get_supabase_config() -> Dict[str, str]:
    """Get Supabase configuration from Parameter Store"""
    
    # Production - get from Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameters(
            Names=[
                f'/pianofi/supabase/url',
                f'/pianofi/supabase/anon_key',
                f'/pianofi/supabase/service_role_key'
            ],
            WithDecryption=True
        )
        
        params = {param['Name'].split('/')[-1]: param['Value'] for param in response['Parameters']}
        
        return {
            "url": params.get("url", ""),
            "anon_key": params.get("anon_key", ""),
            "service_role_key": params.get("service_role_key", "")
        }
    except Exception as e:
        raise Exception(f"Failed to get Supabase config from Parameter Store: {e}")
    
@lru_cache()
def get_backend_base_url() -> str:
    """Get backend base URL from environment"""
    
    # Production - get from Parameter Store or environment
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameter(Name=f'/pianofi/backend/base_url')
        return response['Parameter']['Value']
    except Exception as e:
        # Fallback to environment variable or default
        return os.getenv("BACKEND_BASE_URL", "https://api.pianofi.ca")
    
@lru_cache()
def get_stripe_keys() -> str:
    """Get Stripe keys from Parameter Store"""
    
    # Production - get from Parameter Store
    ssm = boto3.client('ssm', region_name=os.getenv("AWS_REGION", "us-east-1"))
    
    try:
        response = ssm.get_parameters(
            Names=[
                f'/pianofi/stripe/secret_key',
                f'/pianofi/stripe/publishable_key',
                f'/pianofi/stripe/webhook_secret'
            ],
            WithDecryption=True
        )
        
        params = {param['Name'].split('/')[-1]: param['Value'] for param in response['Parameters']}
        
        return {
            "secret_key": params.get("secret_key", ""),
            "publishable_key": params.get("publishable_key", ""),
            "webhook_secret": params.get("webhook_secret", "")
        }
    except Exception as e:
        raise Exception(f"Failed to get Stripe keys from Parameter Store: {e}")

# Configuration class for easy access
class Config:
    DATABASE_URL = get_database_url()
    AWS_CREDENTIALS = get_aws_credentials()
    CORS_ORIGINS = get_cors_origins()
    ENVIRONMENT = get_environment()
    REDIS_URL = get_redis_url()
    SUPABASE_CONFIG = get_supabase_config()
    BACKEND_BASE_URL = get_backend_base_url()
    USE_LOCAL_STORAGE = get_storage()
    STRIPE_KEYS = get_stripe_keys()