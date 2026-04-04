from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import tempfile
import json

from src.core.security import get_current_user, require_role
from src.services.whisper_transcriber import transcriber
from src.core.config import settings

router = APIRouter()

TRANSCRIPTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "transcriptions")
os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)


class TranscriptionResponse(BaseModel):
    consultation_id: str
    transcription: str
    language: str = "es"
    segments: list = []
    created_at: str


class FHIRExtractionResponse(BaseModel):
    bundle: Dict[str, Any]
    confidence: float = 0.85


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    consultation_id: str = Form(...),
    current_user: dict = Depends(require_role(["doctor", "admin"])),
):
    file_content = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    try:
        result = transcriber.transcribe(tmp_path)

        transcription_file = os.path.join(TRANSCRIPTIONS_DIR, f"{consultation_id}.json")
        transcription_data = {
            "consultation_id": consultation_id,
            "transcription": result.text,
            "language": result.language,
            "segments": result.segments,
            "created_at": datetime.now().isoformat(),
            "created_by": current_user["user_id"],
            "reviewed": False,
        }

        with open(transcription_file, "w", encoding="utf-8") as f:
            json.dump(transcription_data, f, ensure_ascii=False, indent=2)

        return TranscriptionResponse(
            consultation_id=consultation_id,
            transcription=result.text,
            language=result.language,
            segments=result.segments,
            created_at=transcription_data["created_at"],
        )

    finally:
        os.unlink(tmp_path)


@router.post("/extract-fhir", response_model=FHIRExtractionResponse)
async def extract_fhir_entities(
    transcription: str = Form(...),
    patient_id: str = Form(...),
    practitioner_id: str = Form(...),
    current_user: dict = Depends(require_role(["doctor", "admin"])),
):
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now().isoformat(),
        "entry": [
            {
                "resource": {
                    "resourceType": "Encounter",
                    "status": "finished",
                    "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "VR", "display": "virtual"},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "participant": [{"individual": {"reference": f"Practitioner/{practitioner_id}"}}],
                }
            }
        ]
    }

    return FHIRExtractionResponse(bundle=bundle, confidence=0.85)


@router.get("/transcriptions/{consultation_id}")
async def get_transcription(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
):
    transcription_file = os.path.join(TRANSCRIPTIONS_DIR, f"{consultation_id}.json")

    if not os.path.exists(transcription_file):
        return {
            "consultation_id": consultation_id,
            "transcription": None,
            "fhir_bundle": None,
            "reviewed": False,
            "created_at": None,
        }

    with open(transcription_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@router.get("/pending-review")
async def list_pending_review(
    current_user: dict = Depends(require_role(["doctor"])),
):
    pending = []
    for filename in os.listdir(TRANSCRIPTIONS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(TRANSCRIPTIONS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not data.get("reviewed", False):
                pending.append({
                    "consultation_id": data["consultation_id"],
                    "created_at": data.get("created_at"),
                    "transcription_preview": data.get("transcription", "")[:100] + "...",
                })
    return pending


@router.post("/{consultation_id}/review")
async def review_transcription(
    consultation_id: str,
    approved: bool = Form(...),
    corrections: Optional[str] = Form(None),
    current_user: dict = Depends(require_role(["doctor"])),
):
    transcription_file = os.path.join(TRANSCRIPTIONS_DIR, f"{consultation_id}.json")

    if not os.path.exists(transcription_file):
        raise HTTPException(status_code=404, detail="Transcripción no encontrada")

    with open(transcription_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["reviewed"] = True
    data["approved"] = approved
    data["reviewed_by"] = current_user["user_id"]
    data["reviewed_at"] = datetime.now().isoformat()

    if corrections:
        data["corrections"] = corrections

    with open(transcription_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"message": "Transcripción revisada", "approved": approved}
