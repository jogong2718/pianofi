from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    email: str
    email_confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # User metadata from Supabase
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    class Config:
        # Allow arbitrary types (for Supabase User object)
        arbitrary_types_allowed = True
        
    @classmethod
    def from_supabase_user(cls, supabase_user):
        """Convert Supabase User object to our User schema"""
        user_metadata = supabase_user.user_metadata or {}
        
        return cls(
            id=supabase_user.id,
            email=supabase_user.email,
            email_confirmed_at=supabase_user.email_confirmed_at,
            created_at=supabase_user.created_at,
            updated_at=supabase_user.updated_at,
            first_name=user_metadata.get('first_name'),
            last_name=user_metadata.get('last_name')
        )