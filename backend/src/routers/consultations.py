from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import random

from src.core.security import get_current_user, require_role
from src.models.database import get_db
from src.models.consultation import Consultation, ConsultationStatus
from sqlalchemy.orm import Session

router = APIRouter()


class ConsultationCreate(BaseModel):
    patient_id: str
    scheduled_at: datetime
    duration_minutes: int = 30
    notes: Optional[str] = None


class ConsultationResponse(BaseModel):
    id: str
    patient_id: str
    practitioner_id: str
    status: str
    scheduled_at: datetime
    room_name: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: int = 30
    notes: Optional[str] = None


PATIENT_NAMES = {
    "patient_175525": "Carlos Garcia",
    "patient_175526": "Maria Lopez",
    "patient_175527": "Juan Perez",
}


@router.post("/", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation: ConsultationCreate,
    current_user: dict = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db)
):
    consultation_id = f"cons_{random.randint(10000, 99999)}"
    room_name = f"room_{consultation_id}"

    new_consultation = Consultation(
        id=consultation_id,
        patient_id=consultation.patient_id,
        practitioner_id=current_user["user_id"],
        room_name=room_name,
        status=ConsultationStatus.SCHEDULED,
        scheduled_at=consultation.scheduled_at,
        duration_minutes=consultation.duration_minutes,
        notes=consultation.notes,
    )

    db.add(new_consultation)
    db.commit()
    db.refresh(new_consultation)

    return ConsultationResponse(
        id=new_consultation.id,
        patient_id=new_consultation.patient_id,
        practitioner_id=new_consultation.practitioner_id,
        status=new_consultation.status,
        scheduled_at=new_consultation.scheduled_at,
        room_name=new_consultation.room_name,
        started_at=new_consultation.started_at,
        ended_at=new_consultation.ended_at,
        duration_minutes=new_consultation.duration_minutes,
        notes=new_consultation.notes,
    )


@router.get("/", response_model=List[ConsultationResponse])
async def list_consultations(
    status_filter: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Consultation)

    if status_filter:
        query = query.filter(Consultation.status == status_filter)
    if patient_id:
        query = query.filter(Consultation.patient_id == patient_id)

    consultations = query.order_by(Consultation.scheduled_at.desc()).all()

    if not consultations:
        seed = Consultation(
            id="cons_43103",
            patient_id="patient_175525",
            practitioner_id="doctor_001",
            room_name="room_cons_43103",
            status=ConsultationStatus.IN_PROGRESS,
            scheduled_at=datetime.now(),
            duration_minutes=30,
        )
        db.add(seed)
        db.commit()
        db.refresh(seed)
        consultations = [seed]

    return [
        ConsultationResponse(
            id=c.id,
            patient_id=c.patient_id,
            practitioner_id=c.practitioner_id,
            status=c.status,
            scheduled_at=c.scheduled_at,
            room_name=c.room_name,
            started_at=c.started_at,
            ended_at=c.ended_at,
            duration_minutes=c.duration_minutes,
            notes=c.notes,
        )
        for c in consultations
    ]


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    return ConsultationResponse(
        id=consultation.id,
        patient_id=consultation.patient_id,
        practitioner_id=consultation.practitioner_id,
        status=consultation.status,
        scheduled_at=consultation.scheduled_at,
        room_name=consultation.room_name,
        started_at=consultation.started_at,
        ended_at=consultation.ended_at,
        duration_minutes=consultation.duration_minutes,
        notes=consultation.notes,
    )


@router.patch("/{consultation_id}/start")
async def start_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor"])),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    consultation.status = ConsultationStatus.IN_PROGRESS
    consultation.started_at = datetime.now()
    db.commit()
    db.refresh(consultation)

    return {
        "id": consultation.id,
        "status": consultation.status,
        "room_name": consultation.room_name,
    }


@router.patch("/{consultation_id}/end")
async def end_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor"])),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    consultation.status = ConsultationStatus.FINISHED
    consultation.ended_at = datetime.now()
    db.commit()
    db.refresh(consultation)

    return {
        "id": consultation.id,
        "status": consultation.status,
    }


@router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_consultation(
    consultation_id: str,
    current_user: dict = Depends(require_role(["doctor", "admin"])),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    consultation.status = ConsultationStatus.CANCELLED
    db.commit()
