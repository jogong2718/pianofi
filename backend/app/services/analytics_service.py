"""
Analytics Service - Handles metrics and analytics calculations.

Functions for dashboard metrics, usage statistics, and reporting.
Serves routers: getDashboardMetrics
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_dashboard_metrics(
    user_id: str,
    db,
    job_repository,
    payment_repository
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard metrics for a user.
    
    Metrics include:
    - Total transcriptions (all time)
    - Currently processing transcriptions
    - This month's transcriptions
    - Transcriptions left this month (based on subscription limit)
    
    Args:
        user_id: ID of the user (string)
        db: Database session
        job_repository: Repository for job data
        payment_repository: Repository for payment data
    
    Returns:
        Dict containing dashboard metrics:
        - total_transcriptions: Total count
        - processing_count: Jobs in processing or queued status
        - this_month_count: Jobs created this month
        - transcriptions_left: Remaining quota (None means unlimited)
    """
    from datetime import datetime
    
    logger.info(f"Calculating dashboard metrics for user {user_id}")
    
    # Total transcriptions for user
    total_transcriptions = job_repository.count_by_user_id(db, user_id)
    
    # Currently processing
    processing_count = job_repository.count_by_user_id_and_status(
        db, user_id, ['processing', 'queued']
    )
    
    # This month's transcriptions
    first_day_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_count = job_repository.count_by_user_id_since_date(
        db, user_id, first_day_of_month
    )
    
    # Number of transcriptions left this month
    subscription = payment_repository.get_active_subscription(db, user_id)
    monthly_limit = subscription["monthly_transcription_limit"] if subscription else 3  # Default to 3 for free users
    
    # Calculate transcriptions left this month
    transcriptions_left = None if monthly_limit is None else max(0, monthly_limit - this_month_count)

    # Calculate number of times picogen model was used this month
    picogen_usage_count = job_repository.count_model_usage_since_date(
        db, user_id, "picogen", first_day_of_month
    )
    
    return {
        "total_transcriptions": total_transcriptions,
        "processing_count": processing_count,
        "this_month_count": this_month_count,
        "transcriptions_left": transcriptions_left,  # None means unlimited
        "picogen_usage_count": picogen_usage_count
    }
