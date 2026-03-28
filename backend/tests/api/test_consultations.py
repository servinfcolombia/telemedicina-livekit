import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


def test_create_consultation_as_doctor(client, auth_token):
    consultation_data = {
        "patient_id": "patient_123",
        "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "duration_minutes": 30,
        "notes": "Consulta de seguimiento"
    }
    response = client.post(
        "/api/v1/consultations/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=consultation_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "patient_123"
    assert data["status"] == "scheduled"


def test_create_consultation_as_patient_forbidden(client, auth_token):
    pass


def test_list_consultations(client, auth_token):
    response = client.get(
        "/api/v1/consultations/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_consultation_by_id(client, auth_token):
    response = client.get(
        "/api/v1/consultations/cons_123",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == "cons_123"


def test_start_consultation(client, auth_token):
    response = client.patch(
        "/api/v1/consultations/cons_123/start",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert "room_name" in data
    assert "token" in data


def test_end_consultation(client, auth_token):
    response = client.patch(
        "/api/v1/consultations/cons_123/end",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "finished"


def test_cancel_consultation(client, auth_token):
    response = client.delete(
        "/api/v1/consultations/cons_123",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204
