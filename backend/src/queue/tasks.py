from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import json

from src.queue.redis_config import (
    QueueNames,
    enqueue_task,
    update_task_status,
    get_task_status,
    get_redis
)
from agents.worker import TranscriptionPipeline, WhisperWorker
from backend.src.services.fhir_mapper import FHIRMapper


class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


async def process_transcription_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task_data.get("task_id")
    consultation_id = task_data.get("consultation_id")
    audio_url = task_data.get("audio_url")
    
    await update_task_status(
        task_id,
        TaskStatus.PROCESSING,
        started_at=datetime.utcnow().isoformat()
    )
    
    try:
        worker = WhisperWorker()
        pipeline = TranscriptionPipeline()
        
        result = await pipeline.process_audio(
            audio_url=audio_url,
            consultation_id=consultation_id
        )
        
        transcription_result = {
            "consultation_id": result.consultation_id,
            "text": result.text,
            "language": result.language,
            "confidence": result.confidence,
            "duration": result.duration,
            "timestamp": result.timestamp
        }
        
        await update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            completed_at=datetime.utcnow().isoformat(),
            result=json.dumps(transcription_result)
        )
        
        return transcription_result
        
    except Exception as e:
        await update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=str(e),
            failed_at=datetime.utcnow().isoformat()
        )
        raise


async def process_fhir_extraction_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    task_id = task_data.get("task_id")
    consultation_id = task_data.get("consultation_id")
    transcription_text = task_data.get("transcription_text")
    patient_id = task_data.get("patient_id")
    practitioner_id = task_data.get("practitioner_id")
    
    await update_task_status(
        task_id,
        TaskStatus.PROCESSING,
        started_at=datetime.utcnow().isoformat()
    )
    
    try:
        mapper = FHIRMapper()
        
        fhir_bundle = mapper.map_to_fhir(
            transcription=transcription_text,
            patient_id=patient_id,
            practitioner_id=practitioner_id,
            consultation_id=consultation_id,
            start_time=datetime.utcnow()
        )
        
        is_valid, errors = mapper.validate_fhir(fhir_bundle)
        
        result = {
            "bundle": fhir_bundle,
            "is_valid": is_valid,
            "validation_errors": errors
        }
        
        await update_task_status(
            task_id,
            TaskStatus.COMPLETED,
            completed_at=datetime.utcnow().isoformat(),
            result=json.dumps(result)
        )
        
        return result
        
    except Exception as e:
        await update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=str(e),
            failed_at=datetime.utcnow().isoformat()
        )
        raise


async def process_full_pipeline(
    audio_url: str,
    consultation_id: str,
    patient_id: str,
    practitioner_id: str
) -> Dict[str, Any]:
    transcription_task = await enqueue_task(
        QueueNames.TRANSCRIPTION,
        {
            "type": "transcription",
            "audio_url": audio_url,
            "consultation_id": consultation_id
        }
    )
    
    transcription_result = await process_transcription_task({
        "task_id": transcription_task,
        "consultation_id": consultation_id,
        "audio_url": audio_url
    })
    
    fhir_task = await enqueue_task(
        QueueNames.FHIR_EXTRACTION,
        {
            "type": "fhir_extraction",
            "transcription_text": transcription_result["text"],
            "patient_id": patient_id,
            "practitioner_id": practitioner_id,
            "consultation_id": consultation_id
        }
    )
    
    fhir_result = await process_fhir_extraction_task({
        "task_id": fhir_task,
        "transcription_text": transcription_result["text"],
        "patient_id": patient_id,
        "practitioner_id": practitioner_id,
        "consultation_id": consultation_id
    })
    
    return {
        "transcription": transcription_result,
        "fhir_bundle": fhir_result["bundle"],
        "is_valid": fhir_result["is_valid"]
    }


class TaskWorker:
    def __init__(self):
        self.running = False
    
    async def start(self):
        self.running = True
        await self._process_queues()
    
    def stop(self):
        self.running = False
    
    async def _process_queues(self):
        while self.running:
            try:
                redis = await get_redis()
                
                task_id = await redis.brpop(
                    [QueueNames.TRANSCRIPTION, QueueNames.FHIR_EXTRACTION],
                    timeout=5
                )
                
                if task_id:
                    queue_name, task_id = task_id
                    task_data = await redis.hgetall(f"task:{task_id}")
                    
                    if task_data.get("type") == "transcription":
                        await process_transcription_task(task_data)
                    elif task_data.get("type") == "fhir_extraction":
                        await process_fhir_extraction_task(task_data)
                        
            except Exception as e:
                print(f"Worker error: {e}")
                await asyncio.sleep(1)
