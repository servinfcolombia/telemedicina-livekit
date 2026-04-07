from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from src.core.config import settings
from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "patient"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    
    user_data = {
        "id": f"user_{hash(user.email) % 1000000}",
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "hashed_password": hashed_password,
        "is_active": True,
    }
    
    return UserResponse(**user_data)


DEFAULT_PASSWORD_HASH = "$2b$12$RRCVyr30.IL2Vu6S1bvODekmnOvWzgP1BRw/4gTjPNwA2xKMEtkru"

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if "doctor" in form_data.username.lower():
        user_role = "doctor"
    elif "admin" in form_data.username.lower():
        user_role = "admin"
    else:
        user_role = "patient"
    
    user_data = {
        "id": "user_001",
        "email": form_data.username,
        "role": user_role,
        "hashed_password": DEFAULT_PASSWORD_HASH,
    }
    
    if not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user_data["id"], "role": user_data["role"]}
    )
    refresh_token = create_refresh_token(data={"sub": user_data["id"]})
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["user_id"],
        email=f"{current_user['user_id']}@example.com",
        full_name="User",
        role=current_user.get("role", "patient"),
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}
