"""
PowerCortex – FastAPI Application Entry Point

Wires together:
  • CORS middleware  (Flutter ↔ API communication)
  • Request logging middleware
  • MongoDB lifecycle  (startup / shutdown)
  • Auth & User routers
  • OpenAPI / Swagger metadata
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import close_mongo_connection, connect_to_mongo
from .core.rate_limiter import limiter, _rate_limit_exceeded_handler, RateLimitExceeded
from .middleware.logging_middleware import LoggingMiddleware
from .routers import auth_router, user_router, notification_router, forecast_router, transformer_router, fault_router, theft_router, assistant_router, system_health_router, renewable_router, weather_router, report_router, validation_router, insights_router

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("powercortex")


# ── Lifespan (startup / shutdown) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifecycle."""
    logger.info("Connecting to MongoDB at %s …", settings.MONGODB_URL)
    await connect_to_mongo()
    logger.info("MongoDB connected – database: %s", settings.DATABASE_NAME)
    
    # Eagerly pre-load all ML models at startup so they are warm and ready
    # before any API request arrives. This prevents the cold-start timeout
    # that causes "Failed to load KPI" on fresh logins.
    logger.info("Pre-loading ML models (this may take a moment)…")
    try:
        from .utils.model_loader import ModelLoader
        import asyncio
        
        # Run model loading in a thread pool to avoid blocking the async event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ModelLoader.load_model)
        logger.info("✓ Demand LSTM model loaded")
        
        await loop.run_in_executor(None, ModelLoader.load_transformer_model)
        logger.info("✓ Transformer health model loaded")
        
        await loop.run_in_executor(None, ModelLoader.load_fault_model)
        logger.info("✓ Fault detection model loaded")
        
        await loop.run_in_executor(None, ModelLoader.load_theft_model)
        logger.info("✓ Theft detection model loaded")
        
        await loop.run_in_executor(None, ModelLoader.load_system_health_model)
        logger.info("✓ System health model loaded")
        
        logger.info("All ML models pre-loaded successfully.")
    except Exception as e:
        logger.warning("Some models failed to pre-load (will retry on first request): %s", e)
    
    # Auto-seed theft alerts if the collection is nearly empty.
    # This ensures the Theft Detection UI always has data to display,
    # even after a database reset or fresh deployment.
    try:
        from .core.database import get_database
        from .repositories.theft_repository import TheftRepository
        from .services.theft_service import TheftDetectionService
        
        db = get_database()
        theft_count = await db.theft_alerts.count_documents({})
        if theft_count < 5:
            logger.info("Theft alerts collection has only %d docs – auto-seeding…", theft_count)
            settings.ALLOW_DEMO_DATA = True
            theft_repo = TheftRepository(db)
            theft_service = TheftDetectionService(theft_repo)
            await theft_service.seed_initial_theft_alerts()
            logger.info("✓ Theft alerts auto-seeded successfully.")
        else:
            logger.info("Theft alerts collection has %d docs – skipping seed.", theft_count)
    except Exception as e:
        logger.warning("Failed to auto-seed theft alerts: %s", e)
    
    yield
    logger.info("Shutting down MongoDB connection …")
    await close_mongo_connection()
    logger.info("Goodbye.")


# ── App Factory ───────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "PowerCortex – AI-Powered Power Network Analytics Platform\n\n"
        "Authentication & User Management API"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Rate Limiting ─────────────────────────────────────────────
from slowapi.middleware import SlowAPIMiddleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS (allow Flutter app from any origin during dev) ───────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom middleware ─────────────────────────────────────────
app.add_middleware(LoggingMiddleware)

# ── Version Rewrite Middleware ────────────────────────────────
from .middleware.version_middleware import VersionRewriteMiddleware
app.add_middleware(VersionRewriteMiddleware)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(notification_router.router)
app.include_router(forecast_router.router)
app.include_router(transformer_router.router)
app.include_router(fault_router.router)
app.include_router(theft_router.router)
app.include_router(assistant_router.router)
app.include_router(system_health_router.router)
app.include_router(renewable_router.router)
app.include_router(weather_router.router)
app.include_router(report_router.router)
app.include_router(validation_router.router)
app.include_router(insights_router.router)



# ── Health Check ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    """Simple health-check endpoint."""
    return {
        "success": True,
        "message": f"{settings.APP_NAME} v{settings.APP_VERSION} is running",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health-check with MongoDB connectivity verification."""
    from .core.database import get_database
    db_healthy = False
    try:
        db = get_database()
        await db.command("ping")
        db_healthy = True
    except Exception:
        pass

    status_str = "healthy" if db_healthy else "unhealthy"
    response = {
        "success": db_healthy,
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": status_str,
        "checks": {
            "mongodb": "connected" if db_healthy else "unreachable",
        }
    }
    if not db_healthy:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=response)
    return response
