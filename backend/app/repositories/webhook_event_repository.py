"""
Webhook Event Repository - Data access for webhook_events table.

Used by: WebhookService
Table: webhook_events (for idempotency tracking)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
