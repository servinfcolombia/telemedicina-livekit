from typing import Optional
from dataclasses import dataclass


@dataclass
class WhisperConfig:
    model_name: str = "medium"
    model_path: Optional[str] = None
    language: str = "es"
    temperature: float = 0.0
    initial_prompt: Optional[str] = None
    word_timestamps: bool = False
    sample_rate: int = 16000
    n_threads: int = 4
    use_gpu: bool = True
    quantize: bool = True

    @classmethod
    def from_env(cls) -> "WhisperConfig":
        import os
        return cls(
            model_name=os.getenv("WHISPER_MODEL", "medium"),
            model_path=os.getenv("WHISPER_MODEL_PATH"),
            language=os.getenv("WHISPER_LANGUAGE", "es"),
            temperature=float(os.getenv("WHISPER_TEMPERATURE", "0.0")),
            use_gpu=os.getenv("WHISPER_USE_GPU", "1") == "1",
            quantize=os.getenv("WHISPER_QUANTIZE", "1") == "1",
        )


WHISPER_CONFIG = WhisperConfig.from_env()

MEDICAL_PROMPT = (
    "Este audio es una consulta médica. "
    "Transcribe con precisión términos médicos, medicamentos, síntomas y diagnósticos. "
    "Usa puntuación apropiada para texto médico."
)
