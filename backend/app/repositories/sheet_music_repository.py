"""
Sheet Music Repository - Data access for sheet_music table.

Used by: SheetMusicService
Table: sheet_music
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
