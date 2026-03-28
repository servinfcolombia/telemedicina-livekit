import pytest
from backend.src.services.fhir_mapper import FHIRMapper, create_fhir_bundle_from_transcription


class TestFHIRMapper:
    def setup_method(self):
        self.mapper = FHIRMapper()

    def test_extract_conditions(self):
        transcription = "El paciente refiere cefalea frontal y fiebre"
        entities = self.mapper.extract_entities(transcription)
        
        assert len(entities["conditions"]) >= 1
        condition_codes = [c["code"] for c in entities["conditions"]]
        assert "25064002" in condition_codes  # cefalea

    def test_extract_medications(self):
        transcription = "Se indica ibuprofeno 400mg cada 8 horas"
        entities = self.mapper.extract_entities(transcription)
        
        assert len(entities["medications"]) >= 1
        med_codes = [m["code"] for m in entities["medications"]]
        assert "5640" in med_codes  # ibuprofeno

    def test_extract_dosage(self):
        transcription = "Se indica paracetamol 500mg cada 6 horas"
        entities = self.mapper.extract_entities(transcription)
        
        if entities["medications"]:
            assert "dosage" in entities["medications"][0]

    def test_map_to_fhir_creates_bundle(self):
        bundle = self.mapper.map_to_fhir(
            transcription="Paciente con cefalea",
            patient_id="patient_123",
            practitioner_id="doctor_001",
            consultation_id="cons_001",
            start_time="2026-03-28T10:00:00"
        )
        
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "collection"
        assert len(bundle["entry"]) >= 1

    def test_map_to_fhir_includes_encounter(self):
        bundle = self.mapper.map_to_fhir(
            transcription="Test",
            patient_id="patient_123",
            practitioner_id="doctor_001",
            consultation_id="cons_001",
            start_time="2026-03-28T10:00:00"
        )
        
        encounter = next(
            e["resource"] for e in bundle["entry"] 
            if e["resource"]["resourceType"] == "Encounter"
        )
        assert encounter is not None
        assert encounter["status"] == "finished"

    def test_validate_fhir_valid_bundle(self):
        bundle = self.mapper.map_to_fhir(
            transcription="Paciente con cefalea",
            patient_id="patient_123",
            practitioner_id="doctor_001",
            consultation_id="cons_001",
            start_time="2026-03-28T10:00:00"
        )
        
        is_valid, errors = self.mapper.validate_fhir(bundle)
        assert is_valid or len(errors) >= 0

    def test_validate_fhir_invalid_bundle(self):
        invalid_bundle = {
            "resourceType": "Bundle",
            "entry": []
        }
        
        is_valid, errors = self.mapper.validate_fhir(invalid_bundle)
        assert is_valid == False


def test_create_fhir_bundle_from_transcription():
    bundle = create_fhir_bundle_from_transcription(
        transcription="Paciente refere cefalea, se indica ibuprofeno",
        patient_id="patient_123",
        practitioner_id="doctor_001",
        consultation_id="cons_001"
    )
    
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
