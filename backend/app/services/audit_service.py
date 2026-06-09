"""
PowerCortex – Audit Service

Business-logic wrapper around the audit repository.
Provides a simple fire-and-forget ``log_action`` helper.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("powercortex.services.audit")

from ..models.audit_log import AuditAction
from ..repositories.audit_repository import AuditRepository
from ..utils.helpers import utcnow


class AuditService:
    """Audit logging service."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._repo = AuditRepository(db)

    async def log_action(
        self,
        user_id: str,
        action: AuditAction,
        ip_address: str = "0.0.0.0",
    ) -> None:
        """Record an auditable action.

        This is intentionally fire-and-forget — callers ``await`` it
        but failures are silently swallowed so they never block the
        main request flow.
        """
        try:
            await self._repo.create(
                {
                    "user_id": user_id,
                    "action": action.value,
                    "timestamp": utcnow(),
                    "ip_address": ip_address,
                }
            )
        except Exception as e:
            # Audit logging should never crash the request, but we must log the failure
            logger.error(f"Failed to write audit log for user {user_id}: {e}")

    async def get_user_logs(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve audit logs for a given user."""
        return await self._repo.get_logs_for_user(user_id, skip, limit)
