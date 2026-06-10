"""
PowerCortex – Logging Middleware

Logs every HTTP request/response with method, path, status code,
and processing time.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("powercortex.http")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request method, path, status, and latency."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start = time.perf_counter()

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "%s %s from %s – unhandled exception",
                method,
                path,
                client_ip,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d (%.1fms) [%s]",
            method,
            path,
            response.status_code,
            elapsed_ms,
            client_ip,
        )

        # ── Audit Logging ─────────────────────────────────────────────
        try:
            import asyncio
            from ..core.database import get_database
            from ..utils.helpers import utcnow
            db = get_database()
            
            user_id = "anonymous"
            if hasattr(request, "state") and hasattr(request.state, "user"):
                user_id = getattr(request.state.user, "email", "anonymous")
            
            audit_record = {
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "ip_address": client_ip,
                "user_id": user_id,
                "timestamp": utcnow(),
                "elapsed_ms": elapsed_ms
            }
            asyncio.create_task(db.audit_logs.insert_one(audit_record))
        except Exception as e:
            logger.debug(f"Failed to record audit log: {e}")

        return response
