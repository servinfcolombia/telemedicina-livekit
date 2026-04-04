import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def doctor_token(client):
    from src.core.security import create_access_token
    return create_access_token(data={"sub": "doctor_001", "role": "doctor"})
