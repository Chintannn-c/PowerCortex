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
from .routers import auth_router, user_router, notification_router, forecast_router, transformer_router, fault_router, theft_router, assistant_router, system_health_router, renewable_router, weather_router, report_router, validation_router

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
    
    # Load ML forecasting model on startup
    from .utils.model_loader import ModelLoader
    ModelLoader.load_model()
    ModelLoader.load_transformer_model()
    ModelLoader.load_fault_model()
    ModelLoader.load_theft_model()
    ModelLoader.load_system_health_model()
    from .ml.renewable_predictor import RenewablePredictor
    RenewablePredictor.load_models()
    
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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    """Detailed health-check."""
    return {
        "success": True,
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
    }
