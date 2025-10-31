from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config_loader import Config
from app.auth import get_current_user
from app.schemas.user import User
from app.schemas.getDashboardMetrics import DashboardMetrics
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.database import get_db
from app.services import analytics_service
from app.repositories import job_repository, payment_repository

router = APIRouter()

@router.get("/getDashboardMetrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = analytics_service.get_dashboard_metrics(
        user_id=current_user.id,
        db=db,
        job_repository=job_repository,
        payment_repository=payment_repository
    )
    
    return DashboardMetrics(**result)