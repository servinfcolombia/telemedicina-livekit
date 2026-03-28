from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.core.security import get_current_user, require_role

router = APIRouter()


class TranscriptionRequest(BaseModel):
    consultation_id: str
    audio_url: str


class TranscriptionResponse(BaseModel):
    consultation_id: str
    transcription: str
    language: str = "es"
    confidence: float = 0.95


class FHIRExtractionRequest(BaseModel):
    transcription: str
    patient_id: str
    practitioner_id: str


class FHIRExtractionResponse(BaseModel):
    bundle: Dict[str, Any]
    confidence: float = 0.85


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: TranscriptionRequest,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    return TranscriptionResponse(
        consultation_id=request.consultation_id,
        transcription="Transcripción de ejemplo de la consulta médica.",
        language="es",
        confidence=0.95
    )


@router.post("/extract-fhir", response_model=FHIRExtractionResponse)
async def extract_fhir_entities(
    request: FHIRExtractionRequest,
    current_user: dict = Depends(require_role(["doctor", "admin"]))
):
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }
    
    return FHIRExtractionResponse(
        bundle=bundle,
        confidence=0.85
    )


@router.get("/transcriptions/{consultation_id}")
async def get_transcription(
    consultation_id: str,
    current_user: dict = Depends(get_current_user)
):
    return {
        "consultation_id": consultation_id,
        "transcription": "Transcripción de ejemplo.",
        "fhir_bundle": None,
        "reviewed": False,
        "created_at": datetime.now().isoformat()
    }


@router.get("/pending-review")
async def list_pending_review(
    current_user: dict = Depends(require_role(["doctor"]))
):
    return []


@router.post("/{transcription_id}/review")
async def review_transcription(
    transcription_id: str,
    approved: bool,
    corrections: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(require_role(["doctor"]))
):
    return {
        "transcription_id": transcription_id,
        "approved": approved,
        "reviewed_by": current_user["user_id"],
        "reviewed_at": datetime.now().isoformat()
    }
