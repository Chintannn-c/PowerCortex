import logging

logger = logging.getLogger("powercortex.versioning")

class VersionRewriteMiddleware:
    """
    Production-grade ASGI middleware to support backward compatibility for older mobile clients.
    Transparently rewrites legacy `/api/` requests to `/api/v1/` for both HTTP and WebSockets.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            
            # If the path starts with /api/ but NOT /api/v1/, rewrite it
            if path.startswith("/api/") and not path.startswith("/api/v1/"):
                new_path = path.replace("/api/", "/api/v1/", 1)
                logger.info(f"Rewriting legacy {scope['type']} request path: {path} -> {new_path}")
                
                # Rewrite the scope path
                scope["path"] = new_path
                
        await self.app(scope, receive, send)
