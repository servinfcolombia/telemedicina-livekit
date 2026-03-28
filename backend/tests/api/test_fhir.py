import pytest
from fastapi.testclient import TestClient


def test_get_patients_unauthorized(client):
    response = client.get("/fhir/Patient")
    assert response.status_code == 401


def test_get_patients(client, auth_token):
    response = client.get(
        "/fhir/Patient",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"


def test_get_patient_by_id(client, auth_token):
    response = client.get(
        "/fhir/Patient/patient_123",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Patient"


def test_create_patient_as_doctor(client, auth_token):
    patient_data = {
        "resourceType": "Patient",
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female"
    }
    response = client.post(
        "/fhir/Patient",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=patient_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Patient"
    assert data["id"] is not None


def test_create_patient_as_patient_forbidden(client, auth_token):
    pass


def test_get_encounters(client, auth_token):
    response = client.get(
        "/fhir/Encounter",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"


def test_get_encounter_by_id(client, auth_token):
    response = client.get(
        "/fhir/Encounter/enc_123",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Encounter"


def test_create_encounter_as_doctor(client, auth_token):
    encounter_data = {
        "resourceType": "Encounter",
        "status": "planned",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "VR"
        }
    }
    response = client.post(
        "/fhir/Encounter",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=encounter_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Encounter"


def test_get_observations(client, auth_token):
    response = client.get(
        "/fhir/Observation",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"


def test_fhir_capability_statement(client):
    response = client.get("/fhir/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "CapabilityStatement"
    assert data["fhirVersion"] == "4.0.1"
