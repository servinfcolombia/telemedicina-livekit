from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import re


class FHIRMapper:
    SNOMED_CODES = {
        "cefalea": "25064002",
        "dolor de cabeza": "25064002",
        "migraña": "195967001",
        "febrícula": "386661008",
        "fiebre": "386661008",
        "tos": "49727002",
        "náusea": "422587007",
        "vómito": "422400008",
        "dolor abdominal": "21522001",
        "diarrea": "235595009",
    }
    
    RXNORM_CODES = {
        "ibuprofeno": "5640",
        "paracetamol": "161",
        "acetaminofén": "161",
        "amoxicilina": "2670",
        "metformina": "860974",
        "losartán": "197884",
    }
    
    LOINC_CODES = {
        "presión arterial": "85354-9",
        "frecuencia cardíaca": "8867-4",
        "temperatura": "8310-5",
        "frecuencia respiratoria": "9279-1",
        "saturación": "2708-6",
    }

    def __init__(self):
        self.bundle_id = str(uuid.uuid4())

    def extract_entities(self, transcription: str) -> Dict[str, List[Dict[str, Any]]]:
        entities = {
            "conditions": [],
            "medications": [],
            "observations": [],
            "procedures": []
        }
        
        transcription_lower = transcription.lower()
        
        for symptom, code in self.SNOMED_CODES.items():
            if symptom in transcription_lower:
                entities["conditions"].append({
                    "code": code,
                    "display": symptom.title(),
                    "text": symptom,
                    "system": "http://snomed.info/sct"
                })
        
        for medication, code in self.RXNORM_CODES.items():
            if medication in transcription_lower:
                entities["medications"].append({
                    "code": code,
                    "display": medication.title(),
                    "text": medication,
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm"
                })
        
        dosage_pattern = r"(\w+)\s*(\d+)\s*(mg|ml|g|comprimidos?|cápsulas?)"
        for match in re.finditer(dosage_pattern, transcription_lower):
            if entities["medications"]:
                entities["medications"][-1]["dosage"] = match.group(0)
        
        for obs, code in self.LOINC_CODES.items():
            if obs in transcription_lower:
                value = self._extract_value(transcription, obs)
                if value:
                    entities["observations"].append({
                        "code": code,
                        "display": obs.title(),
                        "value": value,
                        "system": "http://loinc.org"
                    })
        
        return entities

    def _extract_value(self, transcription: str, observation: str) -> Optional[float]:
        patterns = {
            "presión arterial": r"(\d{2,3})/(\d{2,3})",
            "frecuencia cardíaca": r"(\d{2,3})\s*(lpm|latidos)",
            "temperatura": r"(\d{2})\s*(°C|grados)",
            "saturación": r"(\d{2,3})\s*%",
        }
        
        pattern = patterns.get(observation)
        if not pattern:
            return None
        
        match = re.search(pattern, transcription.lower())
        if match:
            return float(match.group(1))
        return None

    def map_to_fhir(
        self,
        transcription: str,
        patient_id: str,
        practitioner_id: str,
        consultation_id: str,
        start_time: Union[str, datetime],
        end_time: Optional[Union[str, datetime]] = None
    ) -> Dict[str, Any]:
        entities = self.extract_entities(transcription)
        
        encounter_id = f"enc-{consultation_id}"
        timestamp = datetime.now().isoformat()
        
        start_dt = start_time if isinstance(start_time, datetime) else datetime.fromisoformat(start_time)
        end_dt = end_time if isinstance(end_time, datetime) else (datetime.fromisoformat(end_time) if end_time else datetime.now())
        
        bundle = {
            "resourceType": "Bundle",
            "id": self.bundle_id,
            "meta": {
                "profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"]
            },
            "type": "collection",
            "timestamp": timestamp,
            "entry": []
        }
        
        encounter = {
            "resourceType": "Encounter",
            "id": encounter_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "VR",
                "display": "virtual"
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "participant": [
                {"individual": {"reference": f"Practitioner/{practitioner_id}"}}
            ],
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            }
        }
        
        bundle["entry"].append({
            "fullUrl": f"urn:uuid:{encounter_id}",
            "resource": encounter
        })
        
        for i, condition in enumerate(entities["conditions"]):
            condition_id = f"cond-{consultation_id}-{i}"
            bundle["entry"].append({
                "fullUrl": f"urn:uuid:{condition_id}",
                "resource": {
                    "resourceType": "Condition",
                    "id": condition_id,
                    "clinicalStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active",
                            "display": "Active"
                        }]
                    },
                    "code": {
                        "coding": [{
                            "system": condition["system"],
                            "code": condition["code"],
                            "display": condition["display"]
                        }],
                        "text": condition["text"]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{encounter_id}"}
                }
            })
        
        for i, medication in enumerate(entities["medications"]):
            med_id = f"med-{consultation_id}-{i}"
            med_resource = {
                "resourceType": "MedicationRequest",
                "id": med_id,
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{
                        "system": medication["system"],
                        "code": medication["code"],
                        "display": medication["display"]
                    }],
                    "text": medication["text"]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "authoredOn": timestamp
            }
            
            if "dosage" in medication:
                med_resource["dosageInstruction"] = [{
                    "text": medication["dosage"]
                }]
            
            bundle["entry"].append({
                "fullUrl": f"urn:uuid:{med_id}",
                "resource": med_resource
            })
        
        for i, observation in enumerate(entities["observations"]):
            obs_id = f"obs-{consultation_id}-{i}"
            bundle["entry"].append({
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }]
                    }],
                    "code": {
                        "coding": [{
                            "system": observation["system"],
                            "code": observation["code"],
                            "display": observation["display"]
                        }]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{encounter_id}"},
                    "effectiveDateTime": timestamp,
                    "valueQuantity": {
                        "value": observation["value"],
                        "unit": "%" if "satur" in observation["display"].lower() else "beats/min"
                    }
                }
            })
        
        return bundle

    def validate_fhir(self, bundle: Dict[str, Any]) -> tuple[bool, List[str]]:
        errors = []
        
        if bundle.get("resourceType") != "Bundle":
            errors.append("Root must be a Bundle resource")
        
        if not bundle.get("entry"):
            errors.append("Bundle must contain at least one entry")
        
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if not resource_type:
                errors.append("Each entry must have a resourceType")
                continue
            
            if resource_type == "Encounter":
                if not resource.get("subject"):
                    errors.append("Encounter must have a subject reference")
            
            if resource_type == "Condition":
                if not resource.get("code", {}).get("coding"):
                    errors.append("Condition must have a code with coding")
        
        return len(errors) == 0, errors


def create_fhir_bundle_from_transcription(
    transcription: str,
    patient_id: str,
    practitioner_id: str,
    consultation_id: str
) -> Dict[str, Any]:
    mapper = FHIRMapper()
    return mapper.map_to_fhir(
        transcription=transcription,
        patient_id=patient_id,
        practitioner_id=practitioner_id,
        consultation_id=consultation_id,
        start_time=datetime.now()
    )
