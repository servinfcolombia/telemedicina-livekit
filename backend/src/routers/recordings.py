from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import io
import os
import traceback
import json
import tempfile
import threading

from src.core.security import get_current_user
from src.services.minio_client import get_minio_client, ensure_bucket_exists
from src.core.config import settings

router = APIRouter()

LOCAL_RECORDINGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "recordings"))
os.makedirs(LOCAL_RECORDINGS_DIR, exist_ok=True)
TRANSCRIPTIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "transcriptions"))
os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
print(f"Directorio de grabaciones: {LOCAL_RECORDINGS_DIR}")
print(f"Directorio de transcripciones: {TRANSCRIPTIONS_DIR}")


class RecordingInfo(BaseModel):
    id: str
    consultation_id: str
    file_name: str
    file_size: int
    duration_seconds: int
    uploaded_at: datetime
    uploaded_by: str


@router.post("/", response_model=RecordingInfo, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    file: UploadFile = File(...),
    consultation_id: str = Form(...),
    started_at: str = Form(...),
    duration_seconds: int = Form(0),
    current_user: dict = Depends(get_current_user),
):
    file_content = await file.read()
    file_size = len(file_content)

    object_name = f"{consultation_id}/{uuid.uuid4().hex}_{file.filename or 'recording.webm'}"

    try:
        ensure_bucket_exists()
        client = get_minio_client()
        client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=io.BytesIO(file_content),
            length=file_size,
            content_type=file.content_type or "audio/webm",
        )
        print(f"Grabación guardada en MinIO: {object_name}")
    except Exception as e:
        print(f"Error guardando en MinIO, usando almacenamiento local: {e}")
        traceback.print_exc()

        local_dir = os.path.join(LOCAL_RECORDINGS_DIR, consultation_id)
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, object_name.replace("/", "_"))
        with open(local_path, "wb") as f:
            f.write(file_content)
        print(f"Grabación guardada localmente: {local_path}")

    threading.Thread(
        target=_transcribe_recording_sync,
        args=(file_content, consultation_id, current_user["user_id"]),
        daemon=True,
    ).start()

    return RecordingInfo(
        id=str(uuid.uuid4()),
        consultation_id=consultation_id,
        file_name=object_name,
        file_size=file_size,
        duration_seconds=duration_seconds,
        uploaded_at=datetime.now(),
        uploaded_by=current_user["user_id"],
    )


def _transcribe_recording_sync(file_content: bytes, consultation_id: str, user_id: str):
    """Transcribe recording in background thread after upload."""
    import tempfile
    from src.services.whisper_transcriber import transcriber as whisper_transcriber

    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        print(f"Iniciando transcripción para {consultation_id}...")
        result = whisper_transcriber.transcribe(tmp_path)

        transcription_file = os.path.join(TRANSCRIPTIONS_DIR, f"{consultation_id}.json")
        transcription_data = {
            "consultation_id": consultation_id,
            "transcription": result.text,
            "language": result.language,
            "segments": result.segments,
            "created_at": datetime.now().isoformat(),
            "created_by": user_id,
            "reviewed": False,
        }

        with open(transcription_file, "w", encoding="utf-8") as f:
            json.dump(transcription_data, f, ensure_ascii=False, indent=2)

        print(f"Transcripción completada para {consultation_id}: {len(result.text)} caracteres")

    except Exception as e:
        print(f"Error transcribiendo {consultation_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass


@router.get("/list-all", response_model=list[RecordingInfo])
async def list_all_recordings(
    current_user: dict = Depends(get_current_user),
):
    recordings = []

    if os.path.exists(LOCAL_RECORDINGS_DIR):
        for consultation_id in os.listdir(LOCAL_RECORDINGS_DIR):
            consultation_dir = os.path.join(LOCAL_RECORDINGS_DIR, consultation_id)
            if os.path.isdir(consultation_dir):
                for filename in os.listdir(consultation_dir):
                    filepath = os.path.join(consultation_dir, filename)
                    if os.path.isfile(filepath):
                        file_size = os.path.getsize(filepath)
                        recordings.append(RecordingInfo(
                            id=filename,
                            consultation_id=consultation_id,
                            file_name=filename,
                            file_size=file_size,
                            duration_seconds=0,
                            uploaded_at=datetime.fromtimestamp(os.path.getmtime(filepath)),
                            uploaded_by=current_user["user_id"],
                        ))

    return recordings


@router.get("/{consultation_id}", response_model=list[RecordingInfo])
async def list_recordings(
    consultation_id: str,
    current_user: dict = Depends(get_current_user),
):
    recordings = []

    try:
        ensure_bucket_exists()
        client = get_minio_client()
        objects = client.list_objects(
            bucket_name=settings.MINIO_BUCKET_NAME,
            prefix=f"{consultation_id}/",
        )
        for obj in objects:
            recordings.append(RecordingInfo(
                id=obj.object_name,
                consultation_id=consultation_id,
                file_name=obj.object_name,
                file_size=obj.size or 0,
                duration_seconds=0,
                uploaded_at=obj.last_modified or datetime.now(),
                uploaded_by=current_user["user_id"],
            ))
    except Exception as e:
        print(f"Error listando desde MinIO: {e}")

    local_dir = os.path.join(LOCAL_RECORDINGS_DIR, consultation_id)
    if os.path.exists(local_dir):
        for filename in os.listdir(local_dir):
            filepath = os.path.join(local_dir, filename)
            file_size = os.path.getsize(filepath)
            recordings.append(RecordingInfo(
                id=filename,
                consultation_id=consultation_id,
                file_name=filename,
                file_size=file_size,
                duration_seconds=0,
                uploaded_at=datetime.fromtimestamp(os.path.getmtime(filepath)),
                uploaded_by=current_user["user_id"],
            ))

    return recordings


@router.get("/{consultation_id}/{file_name:path}")
async def download_recording(
    consultation_id: str,
    file_name: str,
    current_user: dict = Depends(get_current_user),
):
    local_path = os.path.join(LOCAL_RECORDINGS_DIR, consultation_id, file_name)
    if os.path.exists(local_path):
        return FileResponse(
            local_path,
            media_type="audio/webm",
            filename=file_name,
        )

    local_path_alt = os.path.join(LOCAL_RECORDINGS_DIR, consultation_id, f"{consultation_id}_{file_name}")
    if os.path.exists(local_path_alt):
        return FileResponse(
            local_path_alt,
            media_type="audio/webm",
            filename=file_name,
        )

    try:
        ensure_bucket_exists()
        client = get_minio_client()
        object_name = f"{consultation_id}/{file_name}"
        response = client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
        )
        return StreamingResponse(
            response,
            media_type="audio/webm",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
    except Exception as e:
        print(f"Error descargando: {e}")
        raise HTTPException(status_code=404, detail="Grabación no encontrada")
