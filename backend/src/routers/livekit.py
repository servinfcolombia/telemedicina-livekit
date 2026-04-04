from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.services.livekit_client import livekit_client
from src.core.config import settings

router = APIRouter()


class TokenRequest(BaseModel):
    roomName: str
    userName: str
    userIdentity: str


class TokenResponse(BaseModel):
    token: str


class IceServerResponse(BaseModel):
    iceServers: list


@router.post("/token", response_model=TokenResponse)
async def generate_token(request: TokenRequest):
    try:
        role = "doctor" if "doctor" in request.userIdentity.lower() else "publisher"
        
        token = livekit_client.generate_token(
            room_name=request.roomName,
            identity=request.userIdentity,
            name=request.userName,
            role=role
        )
        
        return TokenResponse(token=token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate token: {str(e)}"
        )


@router.get("/ice-servers", response_model=IceServerResponse)
async def get_ice_servers():
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET
    
    return IceServerResponse(
        iceServers=[
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
            {"urls": ["turn:openrelay.metered.ca:443"], "username": "openrelayproject", "credential": "openrelayproject"},
        ]
    )
