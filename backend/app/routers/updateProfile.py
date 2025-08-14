from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.schemas.user import User
from app.schemas.updateProfile import UpdateProfileRequest, UpdateProfileResponse
from app.config_loader import Config
from sqlalchemy import text
from app.database import get_db
import logging

router = APIRouter()

@router.put("/updateProfile", response_model=UpdateProfileResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Update database (but don't commit yet)
        update_sql = text("""
            UPDATE users 
            SET first_name = :first_name, last_name = :last_name
            WHERE id = :user_id
        """)
        
        result = db.execute(update_sql, {
            "first_name": profile_data.first_name,
            "last_name": profile_data.last_name,
            "user_id": current_user.id
        })
        
        if result.rowcount == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="User not found")
        
        db.commit()

        user_sql = text("""
            SELECT id, first_name, last_name, created_at
            FROM users 
            WHERE id = :user_id
        """)
        
        user_result = db.execute(user_sql, {"user_id": current_user.id})
        user_row = user_result.fetchone()
        
        user_data = {
            "id": str(user_row[0]),
            "first_name": user_row[1],
            "last_name": user_row[2],
            "created_at": user_row[3].isoformat() if user_row[3] else None,
            "email": current_user.email
        }
        
        logging.info(f"Profile updated for user {current_user.id}")
        return UpdateProfileResponse(
            success=True,
            message="Profile updated successfully",
            user=user_data
        )
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating profile for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")