from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.schemas.user import User
from app.schemas.updateProfile import UpdateProfileRequest, UpdateProfileResponse
from app.database import get_db
from app.services import user_service
from app.repositories import user_repository
import logging

router = APIRouter()

@router.put("/updateProfile", response_model=UpdateProfileResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Call service to handle the update logic
        result = user_service.update_profile(
            user_id=current_user.id,
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            email=current_user.email,
            db=db,
            user_repository=user_repository
        )

        print("update profile works")
        
        return UpdateProfileResponse(**result)
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating profile for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")