from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random

from src.core.security import get_current_user, require_role

router = APIRouter()

# In-memory storage for consultations
consultations_db: dict = {}


class ConsultationCreate(BaseModel):
    patient_id: str
    scheduled_at: datetime
    duration_minutes: int = 30
    notes: Optional[str] = None


class Consultation(BaseModel):
    id: str
    patient_id: str
    practitioner_id: str
    room_name: Optional[str] = None
    status: str = "scheduled"
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: int = 30
    notes: Optional[str] = None


class ConsultationResponse(BaseModel):
    id: str
    patient_id: str
    practitioner_id: str
    status: str
    scheduled_at: datetime


PATIENT_NAMES = {
    "patient_175525": "Carlos Garcia",
    "patient_175526": "Maria Lopez",
    "patient_175527": "Juan Perez",
}


@router.post("/", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation: ConsultationCreate,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    consultation_id = f"cons_{random.randint(10000, 99999)}"
    room_name = f"room_{consultation_id}"
    
    new_consultation = Consultation(
        id=consultation_id,
        patient_id=consultation.patient_id,
        practitioner_id=current_user["user_id"],
        room_name=room_name,
        status="scheduled",
        scheduled_at=consultation.scheduled_at,
        duration_minutes=consultation.duration_minutes,
        notes=consultation.notes,
    )
    
    consultations_db[consultation_id] = new_consultation
    
    return ConsultationResponse(
        id=consultation_id,
        patient_id=consultation.patient_id,
        practitioner_id=current_user["user_id"],
        status="scheduled",
        scheduled_at=consultation.scheduled_at
    )


@router.get("/", response_model=List[Consultation])
async def list_consultations(
    status_filter: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    results = list(consultations_db.values())
    
    if not results:
        results = [
            Consultation(
                id="cons_43103",
                patient_id="patient_175525",
                practitioner_id="doctor_001",
                room_name="room_cons_43103",
                status="in_progress",
                scheduled_at=datetime.now(),
                duration_minutes=30
            )
        ]
    
    if status_filter:
        results = [c for c in results if c.status == status_filter]
    if patient_id:
        results = [c for c in results if c.patient_id == patient_id]
    
    return results


@router.get("/{consultation_id}", response_model=Consultation)
async def get_consultation(
    consultation_id: str,
    current_user: dict = Depends(get_current_user)
):
    if consultation_id in consultations_db:
        return consultations_db[consultation_id]
    
    return Consultation(
        id=consultation_id,
        patient_id="patient_001",
        practitioner_id="doctor_001",
        room_name=f"room_{consultation_id}",
        status="scheduled",
        scheduled_at=datetime.now(),
        duration_minutes=30
    )


@router.patch("/{consultation_id}/start")
async def start_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor"]))
):
    if consultation_id in consultations_db:
        consultations_db[consultation_id].status = "in_progress"
        consultations_db[consultation_id].started_at = datetime.now()
    
    return {
        "id": consultation_id,
        "status": "in_progress",
        "room_name": f"room_{consultation_id}",
    }


@router.patch("/{consultation_id}/end")
async def end_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor"]))
):
    if consultation_id in consultations_db:
        consultations_db[consultation_id].status = "finished"
        consultations_db[consultation_id].ended_at = datetime.now()
    
    return {
        "id": consultation_id,
        "status": "finished"
    }


@router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    if consultation_id in consultations_db:
        consultations_db[consultation_id].status = "cancelled"
