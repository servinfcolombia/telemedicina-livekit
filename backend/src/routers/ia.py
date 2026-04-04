from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import tempfile
import json

from src.core.security import get_current_user, require_role
from src.services.whisper_transcriber import transcriber
from src.services.fhir_mapper import FHIRMapper
from src.core.config import settings
from src.models.database import get_db
from src.models.consultation import Transcription
from sqlalchemy.orm import Session

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
    entities: Dict[str, List[Dict[str, Any]]]


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
    consultation_id: str = Form(""),
    current_user: dict = Depends(require_role(["doctor", "admin"])),
):
    mapper = FHIRMapper()
    entities = mapper.extract_entities(transcription)

    bundle = mapper.map_to_fhir(
        transcription=transcription,
        patient_id=patient_id,
        practitioner_id=practitioner_id,
        consultation_id=consultation_id or "unknown",
        start_time=datetime.now(),
    )

    is_valid, errors = mapper.validate_fhir(bundle)

    total_entities = (
        len(entities["conditions"])
        + len(entities["medications"])
        + len(entities["observations"])
        + len(entities["procedures"])
    )
    confidence = max(0.5, min(1.0, total_entities * 0.2))

    return FHIRExtractionResponse(
        bundle=bundle,
        confidence=round(confidence, 2),
        entities=entities,
    )


@router.get("/fhir/{consultation_id}")
async def get_fhir_bundle(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transcription = db.query(Transcription).filter(Transcription.consultation_id == consultation_id).first()

    transcription_text = None
    fhir_entities = None
    fhir_bundle = None

    if transcription and transcription.transcription_text:
        transcription_text = transcription.transcription_text

        if transcription.fhir_entities:
            try:
                fhir_entities = json.loads(transcription.fhir_entities)
            except:
                pass
        if transcription.fhir_bundle:
            try:
                fhir_bundle = json.loads(transcription.fhir_bundle)
            except:
                pass

    if not transcription_text:
        transcription_file = os.path.join(TRANSCRIPTIONS_DIR, f"{consultation_id}.json")
        if os.path.exists(transcription_file):
            with open(transcription_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            transcription_text = data.get("transcription", "")
            fhir_entities = data.get("fhir_entities")
            fhir_bundle = data.get("fhir_bundle")

    if not transcription_text or transcription_text.startswith("Error"):
        return {"bundle": None, "entities": None}

    if not fhir_entities:
        mapper = FHIRMapper()
        fhir_entities = mapper.extract_entities(transcription_text)

    total_entries = (
        len(fhir_entities.get("conditions", []))
        + len(fhir_entities.get("medications", []))
        + len(fhir_entities.get("observations", []))
        + len(fhir_entities.get("procedures", []))
    )

    if not fhir_bundle and total_entries > 0:
        mapper = FHIRMapper()
        fhir_bundle = mapper.map_to_fhir(
            transcription=transcription_text,
            patient_id="unknown",
            practitioner_id="unknown",
            consultation_id=consultation_id,
            start_time=datetime.now(),
        )

    return {
        "bundle": fhir_bundle,
        "entities": fhir_entities,
        "total_entities": total_entries,
    }


@router.get("/transcriptions/{consultation_id}")
async def get_transcription(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transcription = db.query(Transcription).filter(Transcription.consultation_id == consultation_id).first()

    if not transcription:
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

    result = {
        "consultation_id": transcription.consultation_id,
        "transcription": transcription.transcription_text,
        "language": transcription.language,
        "segments": json.loads(transcription.segments) if transcription.segments else [],
        "created_at": transcription.created_at.isoformat() if transcription.created_at else None,
        "created_by": transcription.created_by,
        "reviewed": transcription.reviewed,
        "approved": transcription.approved,
        "reviewed_by": transcription.reviewed_by,
        "reviewed_at": transcription.reviewed_at.isoformat() if transcription.reviewed_at else None,
        "corrections": transcription.corrections,
    }

    if transcription.fhir_bundle:
        result["fhir_bundle"] = json.loads(transcription.fhir_bundle)
    if transcription.fhir_entities:
        result["fhir_entities"] = json.loads(transcription.fhir_entities)
    if transcription.fhir_valid is not None:
        result["fhir_valid"] = transcription.fhir_valid

    return result


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
    db: Session = Depends(get_db),
):
    transcription = db.query(Transcription).filter(Transcription.consultation_id == consultation_id).first()

    if transcription:
        transcription.reviewed = True
        transcription.approved = approved
        transcription.reviewed_by = current_user["user_id"]
        transcription.reviewed_at = datetime.now()
        if corrections:
            transcription.corrections = corrections
        db.commit()

    transcription_file = os.path.join(TRANSCRIPTIONS_DIR, f"{consultation_id}.json")
    if os.path.exists(transcription_file):
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
