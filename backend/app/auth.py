from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.config import Config
import os

security = HTTPBearer()

# Supabase client for auth verification
def get_supabase_client():
    supabase_config = Config.SUPABASE_CONFIG
    
    if not supabase_config["url"] or not supabase_config["anon_key"]:
        raise Exception("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    
    return create_client(supabase_config["url"], supabase_config["anon_key"])

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Extract and validate user from JWT token
    Returns the authenticated user's data
    """
    try:
        # Get JWT token from Authorization header
        token = credentials.credentials
        
        # Create Supabase client and verify token
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return response.user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )