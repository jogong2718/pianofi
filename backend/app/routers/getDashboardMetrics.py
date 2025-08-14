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

router = APIRouter()

@router.get("/getDashboardMetrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Total transcriptions for user
    total_result = db.execute(
        text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id"),
        {"user_id": current_user.id}
    )
    total_transcriptions = total_result.scalar()
    
    # Currently processing
    processing_result = db.execute(
        text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id AND status IN ('processing', 'queued')"),
        {"user_id": current_user.id}
    )
    processing_count = processing_result.scalar()
    
    # This month's transcriptions
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_result = db.execute(
        text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id AND created_at >= :start_date"),
        {"user_id": current_user.id, "start_date": first_day_of_month}
    )
    this_month_count = month_result.scalar()
    
    # Number of transcriptions left this month
    subscription_result = db.execute(
        text("""
            SELECT p.monthly_transcription_limit 
            FROM subscriptions s
            JOIN prices p ON s.price_id = p.id
            WHERE s.user_id = :user_id 
            AND s.status = 'active'
            ORDER BY s.created_at DESC
            LIMIT 1
        """),
        {"user_id": current_user.id}
    )

    subscription_row = subscription_result.fetchone()
    monthly_limit = subscription_row[0] if subscription_row else 1  # Default to 1 for free users
    
    # Calculate transcriptions left this month
    transcriptions_left = None if monthly_limit is None else max(0, monthly_limit - this_month_count)
    
    return DashboardMetrics(
        total_transcriptions=total_transcriptions,
        processing_count=processing_count,
        this_month_count=this_month_count,
        transcriptions_left=transcriptions_left  # None means unlimited
    )