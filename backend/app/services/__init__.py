"""
Service layer for business logic.

Services orchestrate business operations by coordinating repositories,
integrations, and domain logic. They should be the primary entry point
for routers and should not contain HTTP-specific logic.

This module uses plain functions instead of classes for simplicity.
Each service file exports functions that can be imported and used directly.
"""

# Import all service functions for easy access
from . import job_service
from . import storage_service
from . import payment_service
from . import user_service
from . import webhook_service
from . import sheet_music_service
from . import analytics_service

__all__ = [
    "job_service",
    "storage_service",
    "payment_service",
    "user_service",
    "webhook_service",
    "sheet_music_service",
    "analytics_service",
]
