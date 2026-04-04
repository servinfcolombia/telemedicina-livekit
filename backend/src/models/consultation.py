from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.models.database import Base


class ConsultationStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(String, primary_key=True, default=lambda: f"cons_{uuid.uuid4().hex[:5]}")
    patient_id = Column(String, nullable=False, index=True)
    practitioner_id = Column(String, nullable=False, index=True)
    room_name = Column(String, unique=True, nullable=True)
    status = Column(SAEnum(ConsultationStatus), default=ConsultationStatus.SCHEDULED, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=30)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transcription = relationship("Transcription", back_populates="consultation", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Consultation {self.id} - {self.status}>"


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True, default=lambda: f"trans_{uuid.uuid4().hex[:8]}")
    consultation_id = Column(String, ForeignKey("consultations.id"), unique=True, nullable=False, index=True)
    transcription_text = Column(Text, nullable=True)
    language = Column(String, default="es")
    segments = Column(Text, nullable=True)
    fhir_bundle = Column(Text, nullable=True)
    fhir_entities = Column(Text, nullable=True)
    fhir_valid = Column(Boolean, default=False)
    created_by = Column(String, nullable=False)
    reviewed = Column(Boolean, default=False)
    approved = Column(Boolean, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    corrections = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    consultation = relationship("Consultation", back_populates="transcription")

    def __repr__(self):
        return f"<Transcription {self.consultation_id}>"


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(String, primary_key=True, default=lambda: f"rec_{uuid.uuid4().hex[:8]}")
    consultation_id = Column(String, ForeignKey("consultations.id"), nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, default=0)
    storage_type = Column(String, default="local")
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Recording {self.consultation_id}>"
