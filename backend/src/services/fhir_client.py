from typing import Optional, Dict, Any, List
import httpx

from src.core.config import settings


class FHIRClient:
    def __init__(self):
        self.base_url = settings.OPENEMR_FHIR_URL
        self.client_id = settings.OPENEMR_CLIENT_ID
        self.client_secret = settings.OPENEMR_CLIENT_SECRET
        self._token: Optional[str] = None
    
    async def _get_token(self) -> str:
        if not self._token:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                )
                self._token = response.json().get("access_token")
        return self._token
    
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        token = await self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                **kwargs
            )
            return response.json()
    
    async def get_patient(self, patient_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/Patient/{patient_id}")
    
    async def search_patients(self, **params) -> Dict[str, Any]:
        return await self._request("GET", "/Patient", params=params)
    
    async def create_patient(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/Patient", json=patient)
    
    async def update_patient(self, patient_id: str, patient: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"/Patient/{patient_id}", json=patient)
    
    async def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/Encounter/{encounter_id}")
    
    async def search_encounters(self, **params) -> Dict[str, Any]:
        return await self._request("GET", "/Encounter", params=params)
    
    async def create_encounter(self, encounter: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/Encounter", json=encounter)
    
    async def get_observation(self, observation_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/Observation/{observation_id}")
    
    async def search_observations(self, **params) -> Dict[str, Any]:
        return await self._request("GET", "/Observation", params=params)
    
    async def create_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "/Observation", json=observation)


fhir_client = FHIRClient()
