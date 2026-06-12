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
        EXCLUDED_AUDIT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}
        if path not in EXCLUDED_AUDIT_PATHS and not path.startswith("/static/"):
            try:
                import asyncio
                from ..core.database import get_database
                from ..utils.helpers import utcnow
                db = get_database()
                
                user_id = "anonymous"
                if hasattr(request, "state") and hasattr(request.state, "user"):
                    user = request.state.user
                    if isinstance(user, dict):
                        user_id = user.get("email", "anonymous")
                    elif hasattr(user, "email"):
                        user_id = getattr(user, "email", "anonymous")
                    elif isinstance(user, str):
                        user_id = user
                
                audit_record = {
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "ip_address": client_ip,
                    "user_id": user_id,
                    "timestamp": utcnow(),
                    "elapsed_ms": elapsed_ms
                }
                
                async def insert_audit_log():
                    await db.audit_logs.insert_one(audit_record)

                task = asyncio.create_task(insert_audit_log())
                
                def handle_audit_error(t):
                    try:
                        if t.cancelled():
                            return
                        t.result()
                    except Exception as ex:
                        logger.error(f"Background audit log write failed: {ex}")
                        
                task.add_done_callback(handle_audit_error)
            except Exception as e:
                logger.debug(f"Failed to initiate audit log task: {e}")

        return response
