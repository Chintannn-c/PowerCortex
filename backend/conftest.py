import pytest
import asyncio
from fastapi.testclient import TestClient
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
