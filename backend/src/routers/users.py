from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from src.models.database import get_db
from src.models.user import User, UserRole
from src.core.config import settings

router = APIRouter()


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.PACIENTE
    phone: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    role_display: str
    is_active: bool
    is_verified: bool
    phone: Optional[str]
    specialty: Optional[str]
    license_number: Optional[str]
    document_type: Optional[str]
    document_number: Optional[str]
    birth_date: Optional[str]
    gender: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    blood_type: Optional[str]
    allergies: Optional[str]
    medical_history: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        specialty=user_data.specialty,
        license_number=user_data.license_number,
        document_type=user_data.document_type,
        document_number=user_data.document_number,
        birth_date=user_data.birth_date,
        gender=user_data.gender,
        address=user_data.address,
        emergency_contact=user_data.emergency_contact,
        emergency_phone=user_data.emergency_phone,
        blood_type=user_data.blood_type,
        allergies=user_data.allergies,
        medical_history=user_data.medical_history,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        role_display=user.role_display,
        is_active=user.is_active,
        is_verified=user.is_verified,
        phone=user.phone,
        specialty=user.specialty,
        license_number=user.license_number,
        document_type=user.document_type,
        document_number=user.document_number,
        birth_date=user.birth_date,
        gender=user.gender,
        address=user.address,
        emergency_contact=user.emergency_contact,
        emergency_phone=user.emergency_phone,
        blood_type=user.blood_type,
        allergies=user.allergies,
        medical_history=user.medical_history,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    refresh_token = create_access_token(data={"sub": user.id, "type": "refresh"})
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.document_number.ilike(f"%{search}%"),
            )
        )
    
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            role_display=u.role_display,
            is_active=u.is_active,
            is_verified=u.is_verified,
            phone=u.phone,
            specialty=u.specialty,
            license_number=u.license_number,
            document_type=u.document_type,
            document_number=u.document_number,
            birth_date=u.birth_date,
            gender=u.gender,
            address=u.address,
            emergency_contact=u.emergency_contact,
            emergency_phone=u.emergency_phone,
            blood_type=u.blood_type,
            allergies=u.allergies,
            medical_history=u.medical_history,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        role_display=user.role_display,
        is_active=user.is_active,
        is_verified=user.is_verified,
        phone=user.phone,
        specialty=user.specialty,
        license_number=user.license_number,
        document_type=user.document_type,
        document_number=user.document_number,
        birth_date=user.birth_date,
        gender=user.gender,
        address=user.address,
        emergency_contact=user.emergency_contact,
        emergency_phone=user.emergency_phone,
        blood_type=user.blood_type,
        allergies=user.allergies,
        medical_history=user.medical_history,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        role_display=user.role_display,
        is_active=user.is_active,
        is_verified=user.is_verified,
        phone=user.phone,
        specialty=user.specialty,
        license_number=user.license_number,
        document_type=user.document_type,
        document_number=user.document_number,
        birth_date=user.birth_date,
        gender=user.gender,
        address=user.address,
        emergency_contact=user.emergency_contact,
        emergency_phone=user.emergency_phone,
        blood_type=user.blood_type,
        allergies=user.allergies,
        medical_history=user.medical_history,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("user_id") == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    return None


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Contraseña cambiada exitosamente"}


@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        role_display=user.role_display,
        is_active=user.is_active,
        is_verified=user.is_verified,
        phone=user.phone,
        specialty=user.specialty,
        license_number=user.license_number,
        document_type=user.document_type,
        document_number=user.document_number,
        birth_date=user.birth_date,
        gender=user.gender,
        address=user.address,
        emergency_contact=user.emergency_contact,
        emergency_phone=user.emergency_phone,
        blood_type=user.blood_type,
        allergies=user.allergies,
        medical_history=user.medical_history,
        created_at=user.created_at,
        last_login=user.last_login,
    )
