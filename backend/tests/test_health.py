from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from app.main import app
from app.db.session import get_db


def test_app_starts_and_health_returns_200(client: TestClient):
    """
    Verify application starts up successfully and /health returns HTTP 200
    with the expected response contract.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "environment" in data
    assert data["app_name"] == "EduTrack"


def test_database_health_returns_connected_when_db_is_available(client: TestClient, db_session_override):
    """
    Verify /health/db returns 200 OK and connected status when database is reachable.
    Uses the in-memory test database session override.
    """
    app.dependency_overrides[get_db] = lambda: db_session_override
    try:
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
    finally:
        app.dependency_overrides.clear()


def test_database_health_returns_503_when_db_fails(client: TestClient):
    """
    Verify /health/db handles database connection failure gracefully:
    - Returns HTTP 503 Service Unavailable
    - Returns consistent error JSON
    - Does not expose credentials, connection strings, or raw exception tracebacks
    """
    mock_session = MagicMock()
    mock_session.execute.side_effect = OperationalError(
        statement="SELECT 1",
        params={},
        orig=Exception("connection to server at 'localhost' failed: Connection refused"),
    )

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        response = client.get("/health/db")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["database"] == "unavailable"
        # Confirm sensitive strings are not leaked in response
        assert "localhost" not in str(data)
        assert "Connection refused" not in str(data)
    finally:
        app.dependency_overrides.clear()

