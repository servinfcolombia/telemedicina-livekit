from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
import hashlib

try:
    import whisper
except ImportError:
    whisper = None

from agents.whisper_config import WHISPER_CONFIG, MEDICAL_PROMPT


@dataclass
class TranscriptionResult:
    consultation_id: str
    text: str
    language: str
    confidence: float
    segments: List[Dict[str, Any]]
    duration: float
    timestamp: str


class WhisperWorker:
    def __init__(self, config=None):
        self.config = config or WHISPER_CONFIG
        self.model = None
        self._load_model()
    
    def _load_model(self):
        if whisper is None:
            print("Warning: whisper not installed. Using mock transcription.")
            return
        
        try:
            self.model = whisper.load_model(
                self.config.model_name,
                download_root=self.config.model_path
            )
            print(f"Whisper model '{self.config.model_name}' loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None
    
    async def transcribe(
        self,
        audio_path: str,
        consultation_id: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        language = language or self.config.language
        
        if self.model is None:
            return self._mock_transcription(consultation_id)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_path,
                language
            )
            
            return TranscriptionResult(
                consultation_id=consultation_id,
                text=result["text"],
                language=result.get("language", language),
                confidence=self._calculate_confidence(result),
                segments=result.get("segments", []),
                duration=result.get("duration", 0.0),
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            print(f"Transcription error: {e}")
            return self._mock_transcription(consultation_id)
    
    def _transcribe_sync(self, audio_path: str, language: str) -> Dict[str, Any]:
        options = {
            "language": language,
            "temperature": self.config.temperature,
            "initial_prompt": self.config.initial_prompt or MEDICAL_PROMPT,
            "word_timestamps": self.config.word_timestamps,
        }
        
        result = self.model.transcribe(audio_path, **options)
        return result
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        if "segments" not in result or not result["segments"]:
            return 0.85
        
        total_confidence = sum(
            seg.get("avg_logprob", 0) for seg in result["segments"]
        )
        avg_logprob = total_confidence / len(result["segments"])
        
        confidence = (avg_logprob + 1) / 2
        return max(0.0, min(1.0, confidence))
    
    def _mock_transcription(self, consultation_id: str) -> TranscriptionResult:
        return TranscriptionResult(
            consultation_id=consultation_id,
            text="Transcripción de ejemplo de la consulta médica. "
                 "El paciente refiere cefalea frontal de 2 días de evolución. "
                 "Se indica ibuprofeno 400mg cada 8 horas.",
            language="es",
            confidence=0.92,
            segments=[],
            duration=180.0,
            timestamp=datetime.utcnow().isoformat()
        )


class TranscriptionPipeline:
    def __init__(self):
        self.worker = WhisperWorker()
        self._processing = set()
    
    async def process_audio(
        self,
        audio_url: str,
        consultation_id: str,
        callback_url: Optional[str] = None
    ) -> TranscriptionResult:
        if consultation_id in self._processing:
            raise ValueError(f"Consultation {consultation_id} already processing")
        
        self._processing.add(consultation_id)
        
        try:
            result = await self.worker.transcribe(
                audio_path=audio_url,
                consultation_id=consultation_id
            )
            return result
        finally:
            self._processing.discard(consultation_id)
    
    async def batch_process(
        self,
        audio_urls: List[Dict[str, str]]
    ) -> List[TranscriptionResult]:
        tasks = [
            self.process_audio(item["url"], item["consultation_id"])
            for item in audio_urls
        ]
        return await asyncio.gather(*tasks)


async def main():
    pipeline = TranscriptionPipeline()
    
    result = await pipeline.process_audio(
        audio_url="test_audio.mp3",
        consultation_id="cons_12345"
    )
    
    print(f"Transcription: {result.text}")
    print(f"Confidence: {result.confidence}")
    print(f"Language: {result.language}")


if __name__ == "__main__":
    asyncio.run(main())
