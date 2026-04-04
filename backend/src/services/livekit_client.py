import os
import time
from typing import Optional, Dict, Any
import jwt
from src.core.config import settings


class LiveKitClient:
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.url = settings.LIVEKIT_URL
    
    def generate_token(
        self,
        room_name: str,
        identity: str,
        name: str,
        role: str = "publisher"
    ) -> str:
        now = int(time.time())
        exp = now + 3600
        
        video_grants = {
            "roomJoin": True,
            "room": room_name,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
            "canUpdateOwnMetadata": True,
        }
        
        payload = {
            "iss": self.api_key,
            "sub": identity,
            "name": name,
            "exp": exp,
            "nbf": now,
            "video": video_grants,
            "metadata": "",
        }
        
        token = jwt.encode(payload, self.api_secret, algorithm="HS256")
        return token
    
    async def create_room(self, room_name: str, max_participants: int = 4) -> Dict[str, Any]:
        return {"room_name": room_name, "max_participants": max_participants}
    
    async def delete_room(self, room_name: str) -> bool:
        return True

    async def list_rooms(self) -> list:
        return []
    
    async def get_room(self, room_name: str) -> Optional[Dict[str, Any]]:
        return {"room_name": room_name, "status": "active"}
    
    async def start_recording(self, room_name: str, output_path: str) -> str:
        return f"recording_{room_name}_{hash(output_path) % 100000}"
    
    async def stop_recording(self, recording_id: str) -> bool:
        return True


livekit_client = LiveKitClient()
