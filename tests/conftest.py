import pytest
from mongomock_motor import AsyncMongoMockClient
from pymongo.collection import Collection
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.db import MongoDB, get_collection
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def mock_db():
    """Fixture que simula el cliente MongoDB usando mongomock"""
    try:
        yield AsyncMongoMockClient().test_festivo
    finally:
        AsyncMongoMockClient().close()


@pytest.fixture
def client(mock_db):
    def mock_get_collection(collection_name: str):
        return lambda: mock_db[collection_name]

    app.dependency_overrides[get_collection] = mock_get_collection

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


