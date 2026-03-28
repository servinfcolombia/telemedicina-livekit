from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.core.security import get_current_user, require_role

router = APIRouter()


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


@router.post("/", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation: ConsultationCreate,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    consultation_id = f"cons_{hash(consultation.patient_id) % 100000}"
    
    return ConsultationResponse(
        id=consultation_id,
        patient_id=consultation.patient_id,
        practitioner_id=current_user["user_id"],
        status="scheduled",
        scheduled_at=consultation.scheduled_at
    )


@router.get("/", response_model=List[ConsultationResponse])
async def list_consultations(
    status: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    return []


@router.get("/{consultation_id}", response_model=Consultation)
async def get_consultation(
    consultation_id: str,
    current_user: dict = Depends(get_current_user)
):
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
    return {
        "id": consultation_id,
        "status": "in_progress",
        "room_name": f"room_{consultation_id}",
        "token": f"lk_token_{consultation_id}"
    }


@router.patch("/{consultation_id}/end")
async def end_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor"]))
):
    return {
        "id": consultation_id,
        "status": "finished"
    }


@router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    pass
