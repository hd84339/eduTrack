import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.db.session import get_db

# Optional in-memory SQLite database for isolated unit tests
TEST_SQLITE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    TestClient fixture for standard API integration testing.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session_override() -> Generator[Session, None, None]:
    """
    Provides an active in-memory test database session overriding the default get_db dependency.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

