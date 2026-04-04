import os
import tempfile
import subprocess
import shutil
import httpx
from typing import Optional
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    text: str
    language: str
    segments: list = None


WHISPER_SERVER_URL = os.getenv("WHISPER_SERVER_URL", "http://localhost:9002/asr")


def _find_ffmpeg() -> str:
    common_paths = [
        "ffmpeg",
        "C:\\Users\\Daniela\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1-full_build\\bin\\ffmpeg.exe",
        "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    found = shutil.which("ffmpeg")
    if found:
        return found
    return "ffmpeg"


class WhisperTranscriber:
    def __init__(self, language: str = "es"):
        self.language = language
        self.ffmpeg_path = _find_ffmpeg()

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            file_path = audio_path
            ext = audio_path.rsplit(".", 1)[-1].lower()

            if ext != "wav":
                try:
                    wav_path = self._convert_to_wav(audio_path)
                    if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                        file_path = wav_path
                        print(f"Audio convertido a WAV: {wav_path}")
                    else:
                        print("Conversión a WAV fallida, usando archivo original")
                except Exception as e:
                    print(f"Warning: No se pudo convertir a WAV, enviando original: {e}")

            print(f"Enviando audio a Whisper: {file_path} ({os.path.getsize(file_path)} bytes)")

            with open(file_path, "rb") as f:
                files = {"audio_file": (os.path.basename(file_path), f, "audio/wav")}
                data = {"language": self.language, "task": "transcribe", "output": "json"}

                with httpx.Client(timeout=300.0) as client:
                    response = client.post(WHISPER_SERVER_URL, files=files, data=data)

            if file_path != audio_path and os.path.exists(file_path):
                os.unlink(file_path)

            if response.status_code != 200:
                raise Exception(f"Whisper server error: {response.status_code} - {response.text}")

            content_type = response.headers.get("content-type", "")

            if "json" in content_type:
                json_data = response.json()
                text = json_data.get("transcription", json_data.get("text", ""))
                segments = json_data.get("segments", [])
            else:
                text = response.text.strip()
                segments = []

            print(f"Transcripción exitosa: {len(text)} caracteres")

            return TranscriptionResult(
                text=text.strip(),
                language=self.language,
                segments=segments,
            )

        except httpx.ConnectError:
            print(f"Cannot connect to Whisper server at {WHISPER_SERVER_URL}")
            return TranscriptionResult(
                text="Error: Servicio de transcripción no disponible. Verifica que el contenedor whisper esté corriendo.",
                language=self.language,
            )
        except Exception as e:
            print(f"Error transcribiendo: {e}")
            import traceback
            traceback.print_exc()
            return TranscriptionResult(
                text=f"Error en transcripción: {str(e)}",
                language=self.language,
            )

    def _convert_to_wav(self, audio_path: str) -> str:
        wav_path = audio_path.rsplit(".", 1)[0] + ".wav"
        if not os.path.exists(self.ffmpeg_path):
            raise FileNotFoundError(f"ffmpeg not found at {self.ffmpeg_path}")
        result = subprocess.run([
            self.ffmpeg_path, "-y", "-i", audio_path,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            wav_path
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {result.stderr}")
        return wav_path


transcriber = WhisperTranscriber(language="es")
