from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SAEnum
from datetime import datetime
import uuid
import enum

from src.models.database import Base


class UserRole(str, enum.Enum):
    MEDICO = "medico"
    PACIENTE = "paciente"
    ENFERMERA_JEFE = "enfermera_jefe"
    AUXILIAR_ENFERMERIA = "auxiliar_enfermeria"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:8]}")
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.PACIENTE, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    phone = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    
    document_type = Column(String, nullable=True)
    document_number = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    emergency_contact = Column(String, nullable=True)
    emergency_phone = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.email} - {self.role}>"
    
    @property
    def role_display(self) -> str:
        role_names = {
            UserRole.MEDICO: "Médico",
            UserRole.PACIENTE: "Paciente",
            UserRole.ENFERMERA_JEFE: "Enfermera Jefe",
            UserRole.AUXILIAR_ENFERMERIA: "Auxiliar de Enfermería",
            UserRole.ADMIN: "Administrador",
        }
        return role_names.get(self.role, str(self.role))
    
    @property
    def role_color(self) -> str:
        role_colors = {
            UserRole.MEDICO: "blue",
            UserRole.PACIENTE: "green",
            UserRole.ENFERMERA_JEFE: "purple",
            UserRole.AUXILIAR_ENFERMERIA: "yellow",
            UserRole.ADMIN: "red",
        }
        return role_colors.get(self.role, "gray")
