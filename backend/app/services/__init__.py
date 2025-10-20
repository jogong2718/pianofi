"""
Service layer for business logic.

Services orchestrate business operations by coordinating repositories,
integrations, and domain logic. They should be the primary entry point
for routers and should not contain HTTP-specific logic.

This module uses plain functions instead of classes for simplicity.
Each service file exports functions that can be imported and used directly.
"""

# Import all service functions for easy access
from backend.app.services import job_service
from backend.app.services import storage_service
from backend.app.services import payment_service
from backend.app.services import user_service
from backend.app.services import webhook_service
from backend.app.services import sheet_music_service
from backend.app.services import analytics_service

__all__ = [
    "job_service",
    "storage_service",
    "payment_service",
    "user_service",
    "webhook_service",
    "sheet_music_service",
    "analytics_service",
]
