from typing import Optional, Dict, Any
from livekit import api
from src.core.config import settings


class LiveKitClient:
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.url = settings.LIVEKIT_URL
        self._room_api = api.RoomServiceApi(self.url, self.api_key, self.api_secret)
        self._access_token = api.AccessToken(self.api_key, self.api_secret)
    
    def generate_token(
        self,
        room_name: str,
        identity: str,
        name: str,
        role: str = "publisher"
    ) -> str:
        token = api.AccessToken(self.api_key, self.api_secret)
        token.identity = identity
        token.name = name
        token.add_grant(
            api.RoomGrant(
                room_join=True,
                room=room_name,
                can_publish=role in ["publisher", "doctor"],
                can_subscribe=role in ["subscriber", "publisher", "doctor"],
            )
        )
        return token.to_jwt()
    
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
