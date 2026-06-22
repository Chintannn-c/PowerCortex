import pytest
import asyncio
from fastapi.testclient import TestClient

# ── Isolate tests from production database ──────────────────────
# Override DATABASE_NAME BEFORE any app code reads it, so all
# test-time DB operations target "powercortex_test" instead of the
# production "powercortex" database.  This prevents destructive
# setUp/tearDown calls from wiping live data.
from app.core.config import settings
settings.DATABASE_NAME = "powercortex_test"
settings.ALLOW_DEMO_DATA = True          # allow seed helpers in tests

from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client
