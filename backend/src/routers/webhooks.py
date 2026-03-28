from fastapi import APIRouter, Request, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.core.security import get_current_user

router = APIRouter()


class LiveKitWebhookEvent(BaseModel):
    event: str
    room_name: str
    participant_sid: Optional[str] = None
    participant_identity: Optional[str] = None
    timestamp: Optional[int] = None


class WebhookResponse(BaseModel):
    received: bool
    event: str


@router.post("/livekit", response_model=WebhookResponse)
async def livekit_webhook(request: Request, event: LiveKitWebhookEvent, current_user: dict = Depends(get_current_user)):
    event_data = await request.json()
    
    if event.event == "room_started":
        pass
    elif event.event == "room_finished":
        pass
    elif event.event == "participant_joined":
        pass
    elif event.event == "participant_left":
        pass
    elif event.event == "recording_started":
        pass
    elif event.event == "recording_finished":
        pass
    
    return WebhookResponse(received=True, event=event.event)


@router.get("/events", response_model=list)
async def list_webhook_events(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    return []


@router.post("/test")
async def test_webhook(event: LiveKitWebhookEvent):
    return WebhookResponse(received=True, event=event.event)
