"""
PowerCortex – Async MongoDB Connection

Provides Motor-based async database access and index creation on startup.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings

# ── Module-level client reference ──────────────────────────────
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Open the Motor client and ensure required indexes exist."""
    global _client, _database

    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _database = _client[settings.DATABASE_NAME]

    # ── Create indexes ─────────────────────────────────────────
    await _database.users.create_index("email", unique=True)
    await _database.refresh_tokens.create_index("token", unique=True)
    await _database.refresh_tokens.create_index("user_id")
    await _database.refresh_tokens.create_index("expires_at")
    await _database.audit_logs.create_index("user_id")
    await _database.audit_logs.create_index("timestamp")
    await _database.transformers.create_index("asset_id", unique=True)
    await _database.transformers.create_index("status")
    await _database.faults.create_index("fault_id", unique=True)
    await _database.faults.create_index("status")
    await _database.faults.create_index("detected_at")
    await _database.theft_alerts.create_index("consumer_id", unique=True)
    await _database.theft_alerts.create_index("status")
    await _database.theft_alerts.create_index("is_suspicious")
    await _database.theft_alerts.create_index("created_at")
    await _database.assistant_chats.create_index("user_id")
    await _database.assistant_chats.create_index("timestamp")
    await _database.prediction_validations.create_index("module")
    await _database.prediction_validations.create_index("prediction_id")
    await _database.prediction_validations.create_index("created_at")


async def close_mongo_connection() -> None:
    """Gracefully shut down the Motor client."""
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database handle.

    Raises ``RuntimeError`` if called before ``connect_to_mongo()``.
    """
    if _database is None:
        raise RuntimeError(
            "Database not initialized. Call connect_to_mongo() first."
        )
    return _database
