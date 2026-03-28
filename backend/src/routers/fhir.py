from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.core.security import get_current_user, require_role

router = APIRouter()


class FHIRBundle(BaseModel):
    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int = 0
    entry: List[Dict[str, Any]] = []


class Patient(BaseModel):
    resourceType: str = "Patient"
    id: Optional[str] = None
    name: List[Dict[str, Any]] = []
    gender: Optional[str] = None
    birthDate: Optional[str] = None


class Encounter(BaseModel):
    resourceType: str = "Encounter"
    id: Optional[str] = None
    status: str = "planned"
    class_: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


@router.get("/Patient", response_model=FHIRBundle)
async def get_patients(
    _current_user: dict = Depends(get_current_user)
):
    return FHIRBundle(
        type="searchset",
        total=0,
        entry=[]
    )


@router.get("/Patient/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    return Patient(
        id=patient_id,
        name=[{"family": "Doe", "given": ["John"]}],
        gender="male",
        birthDate="1980-01-01"
    )


@router.post("/Patient", response_model=Patient)
async def create_patient(
    patient: Patient,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    patient.id = f"patient_{hash(patient.name[0].get('family', '')) % 100000}"
    return patient


@router.get("/Encounter", response_model=FHIRBundle)
async def get_encounters(
    patient: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    return FHIRBundle(
        type="searchset",
        total=0,
        entry=[]
    )


@router.get("/Encounter/{encounter_id}", response_model=Encounter)
async def get_encounter(
    encounter_id: str,
    current_user: dict = Depends(get_current_user)
):
    return Encounter(
        id=encounter_id,
        status="finished",
        class_={"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "VR"}
    )


@router.post("/Encounter", response_model=Encounter)
async def create_encounter(
    encounter: Encounter,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    encounter.id = f"encounter_{hash(encounter.status) % 100000}"
    return encounter


@router.get("/Observation", response_model=FHIRBundle)
async def get_observations(
    patient: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    return FHIRBundle(
        type="searchset",
        total=0,
        entry=[]
    )


@router.get("/metadata")
async def fhir_capability():
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "kind": "instance",
        "software": {
            "name": "Telemedicina FHIR Server",
            "version": "1.0.0"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {"type": "Patient", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "Encounter", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "Observation", "interaction": [{"code": "read"}, {"code": "search-type"}]}
            ]
        }]
    }
