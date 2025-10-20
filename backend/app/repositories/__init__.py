"""
Repository layer for data access.

Repositories handle all database operations (CRUD) for domain entities.
They abstract away SQL/ORM details from the service layer.

Each repository file exports functions that operate on a single table/entity.
"""

from backend.app.repositories import job_repository
from backend.app.repositories import user_repository
from backend.app.repositories import payment_repository
from backend.app.repositories import webhook_event_repository
from backend.app.repositories import sheet_music_repository

__all__ = [
    "job_repository",
    "user_repository",
    "payment_repository",
    "webhook_event_repository",
    "sheet_music_repository",
]
