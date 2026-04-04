"""
Seed database from existing JSON transcription files.
Run: cd backend && python scripts/seed_db.py
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))

from src.models.database import engine, Base, SessionLocal
from src.models.consultation import Consultation, ConsultationStatus, Transcription, Recording

Base.metadata.create_all(bind=engine)

TRANSCRIPTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "transcriptions")
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "recordings")

db = SessionLocal()
try:
    seeded_consultations = 0
    seeded_transcriptions = 0
    seeded_recordings = 0

    if os.path.exists(TRANSCRIPTIONS_DIR):
        for filename in os.listdir(TRANSCRIPTIONS_DIR):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(TRANSCRIPTIONS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            consultation_id = data.get("consultation_id", filename.replace(".json", ""))

            existing = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not existing:
                consultation = Consultation(
                    id=consultation_id,
                    patient_id=data.get("patient_id", "patient_unknown"),
                    practitioner_id=data.get("created_by", "user_001"),
                    room_name=f"room_{consultation_id}",
                    status=ConsultationStatus.FINISHED,
                    scheduled_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
                    started_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
                    ended_at=datetime.now(),
                    duration_minutes=30,
                )
                db.add(consultation)
                db.flush()
                seeded_consultations += 1

            existing_trans = db.query(Transcription).filter(Transcription.consultation_id == consultation_id).first()
            if not existing_trans:
                transcription = Transcription(
                    consultation_id=consultation_id,
                    transcription_text=data.get("transcription", ""),
                    language=data.get("language", "es"),
                    segments=json.dumps(data.get("segments", [])),
                    fhir_bundle=json.dumps(data.get("fhir_bundle")),
                    fhir_entities=json.dumps(data.get("fhir_entities")),
                    fhir_valid=data.get("fhir_valid", False),
                    created_by=data.get("created_by", "user_001"),
                    reviewed=data.get("reviewed", False),
                    approved=data.get("approved"),
                    reviewed_by=data.get("reviewed_by"),
                    reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None,
                    corrections=data.get("corrections"),
                    created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
                )
                db.add(transcription)
                seeded_transcriptions += 1

    if os.path.exists(RECORDINGS_DIR):
        for consultation_id in os.listdir(RECORDINGS_DIR):
            consultation_dir = os.path.join(RECORDINGS_DIR, consultation_id)
            if not os.path.isdir(consultation_dir):
                continue

            existing = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not existing:
                consultation = Consultation(
                    id=consultation_id,
                    patient_id="patient_unknown",
                    practitioner_id="user_001",
                    room_name=f"room_{consultation_id}",
                    status=ConsultationStatus.FINISHED,
                    scheduled_at=datetime.now(),
                    duration_minutes=30,
                )
                db.add(consultation)
                db.flush()
                seeded_consultations += 1

            for filename in os.listdir(consultation_dir):
                filepath = os.path.join(consultation_dir, filename)
                if not os.path.isfile(filepath):
                    continue

                existing_rec = db.query(Recording).filter(
                    Recording.consultation_id == consultation_id,
                    Recording.file_name == filename
                ).first()
                if not existing_rec:
                    recording = Recording(
                        consultation_id=consultation_id,
                        file_name=filename,
                        file_path=filepath,
                        file_size=os.path.getsize(filepath),
                        duration_seconds=0,
                        storage_type="local",
                        created_by="user_001",
                    )
                    db.add(recording)
                    seeded_recordings += 1

    db.commit()
    print(f"Database seeded: {seeded_consultations} consultations, {seeded_transcriptions} transcriptions, {seeded_recordings} recordings")

except Exception as e:
    db.rollback()
    print(f"Error seeding database: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
