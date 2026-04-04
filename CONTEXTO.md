# Contexto del Proyecto - Telemedicina

## Estado de la Sesión

**Última sesión**: 03/04/2026
**Directorio de trabajo**: D:\hipocrates
**Estado actual**: Transcripción con Whisper Docker implementada y funcionando

---

## Resumen del Proyecto

Plataforma de telemedicina con:
- Videoconsultas en tiempo real (**PeerJS** - WebRTC P2P)
- **Grabación automática de audio** de cada consulta
- Almacenamiento de grabaciones en **MinIO** (bucket `recordings`)
- **Transcripción automática con Whisper** - Implementada vía Docker (`onerahmet/openai-whisper-asr-webservice`)
- **Extracción FHIR** - Endpoints listos, integración pendiente
- Seguridad HIPAA
- Frontend Next.js 14, Backend FastAPI

---

## Credenciales de Acceso

| Email | Rol | Contraseña |
|-------|-----|------------|
| doctor@test.com | doctor | password123 |
| patient@test.com | patient | password123 |

---

## Credenciales MinIO

| Parámetro | Valor |
|-----------|-------|
| URL | http://localhost:9000 |
| Usuario | minioadmin |
| Contraseña | 51820dacc70cc90c931125cca6274571 |
| Bucket | recordings |

---

## Rutas del Frontend

| Ruta | Descripción |
|------|-------------|
| / | Página principal |
| /auth/signin | Login |
| /dashboard | Dashboard del usuario |
| /consultations | Lista de consultas |
| /consultations/new | Crear nueva consulta |
| /recordings | Lista y descarga grabaciones |
| /room/[roomName] | Sala de videollamada (PeerJS) |

---

## Endpoints API

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/auth/login | Iniciar sesión (form-data: username, password) |
| POST | /api/v1/auth/register | Registrar usuario |
| GET | /api/v1/auth/me | Info del usuario actual |
| POST | /api/v1/auth/logout | Cerrar sesión |
| POST | /api/v1/auth/refresh | Refrescar token |

### Consultas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/v1/consultations/ | Listar consultas |
| POST | /api/v1/consultations/ | Crear consulta (requiere rol: doctor/admin) |
| GET | /api/v1/consultations/{id} | Obtener consulta |
| PATCH | /api/v1/consultations/{id}/start | Iniciar consulta |
| PATCH | /api/v1/consultations/{id}/end | Finalizar consulta |
| DELETE | /api/v1/consultations/{id} | Cancelar consulta |

### Grabaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/recordings/ | Subir grabación de audio |
| GET | /api/v1/recordings/list-all | Listar todas las grabaciones |
| GET | /api/v1/recordings/{consultation_id} | Listar grabaciones de una consulta |
| GET | /api/v1/recordings/{consultation_id}/{file_name} | Descargar grabación |

### IA / Transcripción
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/ia/transcribe | Transcribir audio con Whisper |
| POST | /api/v1/ia/extract-fhir | Extraer entidades FHIR |
| GET | /api/v1/ia/transcriptions/{consultation_id} | Obtener transcripción |
| GET | /api/v1/ia/pending-review | Listar transcripciones pendientes |
| POST | /api/v1/ia/{consultation_id}/review | Aprobar/rechazar transcripción |

### Utilidades
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /health | Estado del backend |
| GET | / | Info del API |

---

## Estado de Servicios

| Servicio | Puerto | Estado |
|----------|--------|--------|
| PostgreSQL | 5433 | Corriendo (Docker) |
| Redis | 6379 | Corriendo (Docker) |
| MinIO | 9000 | Corriendo (Docker, bucket `recordings` creado) |
| Caddy | 80/443 | Corriendo (Docker) |
| LiveKit (Docker) | 7880 | Corriendo (**no usado**) |
| CoTURN (Docker) | 3478 | Corriendo (**no usado**) |
| Backend FastAPI | 8000 | **Iniciar manualmente** |
| Frontend Next.js | 3000 | **Iniciar manualmente** |

---

## Historial Completo de Cambios

### 1. Diagnóstico y Fallo de LiveKit WebRTC

**Problema inicial**: LiveKit fallaba con error "ICE failed, add a TURN server".

**Causas identificadas**:
- CoTURN no reachable desde el navegador (red Docker vs Windows)
- ICE candidates siempre fallidos
- Sin candidatos de tipo "relay" (TURN)
- CoTURN tenía configuración incorrecta (`secret-key` en lugar de `static-auth-secret`)

**Intentos de solución**:
1. Corrección de turnserver.conf (`static-auth-secret`, `max-allocate-lifetime`, `channel-lifetime`)
2. Cambio de ICE servers a DNS interno de Docker (`turn:coturn:3478`)
3. Agregado servidor TURN público (`openrelay.metered.ca:443`)
4. Ninguno funcionó por incompatibilidad de red Docker/Windows

### 2. Intento con Jitsi Meet (Descartado)

**Problema**: Los servicios públicos de Jitsi (`meet.jit.si`, `8x8.vc`) requieren login de Google/GitHub para crear salas.

**Intentos**:
1. Iframe embebido → error de cookies de terceros
2. API externa (`external_api.js`) → error de parseo de JSON en parámetros
3. Ventana nueva (`window.open`) → solicita verificación de cuenta Google
4. Todos descartados

### 3. Implementación de PeerJS (Solución Final)

**Solución**: PeerJS - WebRTC peer-to-peer con servidor de señalización gratuito.

**Ventajas**:
- No requiere cuenta, API key, ni login
- Conexión directa entre navegadores (P2P)
- Sin problemas de cookies de terceros
- Sin restricciones de iframe

**Archivos modificados**:
- `frontend/src/components/video/VideoRoom.tsx` - Componente principal con PeerJS
- `frontend/src/app/room/[roomName]/page.tsx` - Página de sala

**Cómo funciona**:
1. Cada usuario crea un Peer: `telemedicina-{roomName}-{userIdentity}-{timestamp}`
2. Descubrimiento vía `localStorage` con key `peers_telemedicina-{roomName}`
3. Conexión P2P directa para video/audio
4. Polling cada 3 segundos para descubrir nuevos participantes

**Dependencias**:
- `peerjs` (npm package) - instalado en frontend

### 4. Corrección de Roles en Autenticación

**Problema**: El login siempre asignaba rol "patient" a todos los usuarios.
- Causa: `backend/src/routers/auth.py` línea 67 tenía `"role": "patient"` hardcodeado
- Consecuencia: Error 403 "Insufficient permissions" al crear consultas

**Solución**: Detección de rol por email:
```python
if "doctor" in form_data.username.lower():
    user_role = "doctor"
elif "admin" in form_data.username.lower():
    user_role = "admin"
else:
    user_role = "patient"
```

### 5. Consultas Dinámicas

**Problema**: Las consultas creadas no aparecían en la lista (datos estáticos).

**Solución**: `backend/src/routers/consultations.py`:
- Diccionario en memoria `consultations_db`
- POST guarda la consulta
- GET lista las consultas guardadas
- PATCH actualiza estado (in_progress, finished)
- Fallback a datos de ejemplo si no hay consultas

### 6. Grabación de Audio de Consultas

**Frontend** (`VideoRoom.tsx`):
- `MediaRecorder` con formato `audio/webm;codecs=opus`
- Fallback: `audio/webm` → `audio/ogg`
- Graba stream local + agrega tracks remotos dinámicamente
- Indicador rojo "Grabando" con cronómetro
- Al salir (`onstop`), envía blob a `/api/v1/recordings/`

**Backend** (`recordings.py`):
- `POST /` - Recibe FormData (file, consultation_id, started_at, duration_seconds)
- `GET /list-all` - Lista todas las grabaciones
- `GET /{consultation_id}` - Lista por consulta
- `GET /{consultation_id}/{file_name}` - Descarga (FileResponse/StreamingResponse)
- Fallback a almacenamiento local si MinIO falla

**Almacenamiento**:
- **Primario**: MinIO bucket `recordings`, estructura `{consultation_id}/{uuid}_{filename}`
- **Fallback**: `backend/recordings/` en disco local
- Bucket creado con: `docker exec minio mc mb local/recordings`

**Frontend** (`recordings/page.tsx`):
- Página `/recordings` lista todas las grabaciones
- Tabla: consulta, archivo, tamaño, fecha, botón descargar
- Botón "Grabaciones" en página de consultas

### 7. Configuración de MinIO

**Credenciales** (`.env`):
```
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=recordings
```

**Config** (`config.py`):
```python
MINIO_ENDPOINT: str
MINIO_ACCESS_KEY: str
MINIO_SECRET_KEY: str
MINIO_SECURE: bool = False
MINIO_BUCKET_NAME: str = "recordings"
```

**Servicio** (`minio_client.py`):
- Lazy loading (no conecta al importar)
- `get_minio_client()` - Singleton
- `ensure_bucket_exists()` - Try/except para no bloquear startup

### 8. Transcripción Automática con Whisper (Docker)

**Problema anterior**: whispercpp v0.0.17 es incompatible con Python 3.13 (falta módulo `api_cpp2py_export`). Web Speech API solo funciona en Chrome/Edge, no en Firefox.

**Solución**: Servicio Docker `onerahmet/openai-whisper-asr-webservice` que expone API HTTP para transcripción.

**Servicio Docker** (`docker-compose.yml`):
```yaml
whisper:
  image: onerahmet/openai-whisper-asr-webservice:latest
  container_name: whisper
  ports:
    - "9002:9000"  # 9000-9001 ocupados por MinIO
  environment:
    - ASR_MODEL=base
    - ASR_ENGINE=openai_whisper
    - ASR_LANGUAGE=es
  volumes:
    - whisper_models:/root/.cache/whisper
  restart: unless-stopped
  networks:
    - telemedicina
```

**Backend** (`whisper_transcriber.py`):
- Convierte audio webm → wav con ffmpeg (16kHz, mono, pcm_s16le)
- Envía audio al servicio whisper vía HTTP POST (`http://whisper:9000/asr`)
- Recibe transcripción en JSON con texto y segmentos
- Timeout de 300 segundos para audios largos

**Integración automática** (`recordings.py`):
- Al subir grabación, hilo separado envía audio a whisper
- Transcripción se guarda en `backend/transcriptions/{consultation_id}.json`
- Formato: `{consultation_id, transcription, language, segments, created_at, created_by, reviewed}`

**Endpoints IA** (`ia.py`):
- `POST /api/v1/ia/transcribe` - Transcribir audio manualmente
- `POST /api/v1/ia/extract-fhir` - Extraer entidades FHIR
- `GET /api/v1/ia/transcriptions/{consultation_id}` - Obtener transcripción
- `GET /api/v1/ia/pending-review` - Listar transcripciones pendientes
- `POST /api/v1/ia/{consultation_id}/review` - Aprobar/rechazar

**Frontend** (`transcriptions/page.tsx`):
- Página `/transcriptions` lista todas las transcripciones
- Expandir para ver texto completo
- Botones para aprobar/rechazar con correcciones
- Indicadores: Pendiente (amarillo), Aprobada (verde), Rechazada (rojo)
- Botón "Transcripciones" en página de consultas

**Puertos**:
- MinIO: 9000-9001
- Whisper: 9002 (mapeado a 9000 interno)

**Estado**: ✅ Funcionando - Contenedor whisper corriendo, endpoint responde correctamente

---

## Cómo Iniciar los Servicios

### 1. Verificar Docker
```powershell
docker ps
```

### 2. Forzar reinicio del backend (si no responde a Ctrl+C)
```powershell
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### 3. Iniciar Backend
```powershell
cd D:\hipocrates\backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Construir e iniciar Frontend
```powershell
cd D:\hipocrates\frontend
npm run build
npm run start
```

---

## Flujo de Prueba Completo

1. Abrir http://localhost:3000
2. Login: `doctor@test.com` / `password123`
3. Ir a "Nueva Consulta" → seleccionar paciente y fecha → crear
4. Ir a "Mis Consultas" → click "Unirse" en una consulta
5. Ingresar nombre e identidad → "Unirse a la consulta"
6. Se inicia la videollamada con PeerJS + grabación automática (indicador rojo)
7. Abrir otra pestaña, entrar como `patient@test.com` a la misma consulta
8. Al finalizar, click "Salir" → la grabación se sube automáticamente
9. Ir a "Grabaciones" → ver y descargar la grabación
10. La transcripción se genera automáticamente en segundo plano

---

## Estructura de Archivos del Proyecto

### Frontend
```
frontend/src/
├── app/
│   ├── auth/signin/page.tsx      # Login
│   ├── consultations/page.tsx    # Lista de consultas
│   ├── consultations/new/page.tsx # Crear consulta
│   ├── recordings/page.tsx       # Lista/descarga grabaciones
│   └── room/[roomName]/page.tsx  # Sala de videollamada
├── components/video/
│   ├── VideoRoom.tsx             # PeerJS + grabación
│   └── Controls.tsx              # Controles (mic, cámara, salir)
└── lib/
    └── auth.ts                   # NextAuth config
```

### Backend
```
backend/src/
├── main.py                       # FastAPI app + CORS + routers
├── core/
│   ├── config.py                 # Settings (MinIO, JWT, etc.)
│   └── security.py               # JWT, require_role, get_current_user
├── routers/
│   ├── auth.py                   # Login con detección de rol
│   ├── consultations.py          # CRUD consultas (memoria)
│   ├── recordings.py             # Upload/list/download grabaciones + transcripción auto
│   ├── ia.py                     # Transcripción, FHIR, review
│   ├── livekit.py                # Legacy (no usado)
│   ├── fhir.py                   # FHIR endpoints
│   └── webhooks.py               # Webhooks
└── services/
    ├── minio_client.py           # Cliente MinIO (lazy loading)
    └── whisper_transcriber.py    # Servicio de transcripción
```

### Docker
```
docker-compose.yml                # PostgreSQL, Redis, MinIO, Caddy, LiveKit, CoTURN
turnserver.conf                   # CoTURN (corregido)
.env                              # Variables de entorno
```

### Almacenamiento
```
backend/
├── recordings/                   # Grabaciones locales (fallback)
│   └── {consultation_id}/
│       └── {uuid}_{filename}.webm
├── transcriptions/               # Transcripciones
│   └── {consultation_id}.json
└── models/                       # Modelos Whisper (PENDIENTE)
    └── ggml-base.bin             # ⚠️ Requiere descarga manual
```

---

## Notas Técnicas

### PeerJS
- Servidor de señalización público (sin configuración)
- Conexión P2P directa (sin servidor de medios)
- Descubrimiento: `localStorage` + polling 3s
- IDs: `telemedicina-{roomName}-{userIdentity}-{timestamp}`

### Grabación de Audio
- `MediaRecorder` API del navegador
- Formato: `audio/webm;codecs=opus` → `audio/webm` → `audio/ogg`
- Se combina audio local + remoto en un solo stream
- Upload al backend en el evento `onstop`

### MinIO
- Bucket `recordings` creado manualmente
- Acceso web: http://localhost:9000
- Usuario: `minioadmin`
- Contraseña: `51820dacc70cc90c931125cca6274571`

### Autenticación
- NextAuth con estrategia JWT
- Token expira en 15 minutos
- Roles detectados por email en backend
- `session.accessToken` = JWT del backend

### Whisper (Docker)
- Imagen: `onerahmet/openai-whisper-asr-webservice:latest`
- Modelo: `base` (español) - descargado automáticamente en el contenedor
- Puerto: 9002 (externo) → 9000 (interno)
- Backend envía audio wav vía HTTP POST a `http://whisper:9000/asr`
- Transcripción en hilo separado (no bloquea)
- Timeout: 300 segundos

---

## Pendientes

1. **Extracción FHIR completa** - El endpoint `/api/v1/ia/extract-fhir` tiene implementación básica (solo crea Encounter)
2. **Persistencia en base de datos** - Consultas y transcripciones están en memoria/archivos locales
3. **MinIO** - SignatureDoesNotMatch, las grabaciones se guardan localmente

---

## Problemas Conocidos

1. **MinIO SignatureDoesNotMatch** - Credenciales no coinciden con Docker, se usa fallback local
2. LiveKit y CoTURN corren en Docker pero no se usan
3. Servicio Jitsi local en docker-compose no configurado
4. Se requiere internet para PeerJS (señalización)
5. Consultas se pierden al reiniciar el backend (almacenamiento en memoria)

---

*Actualizado: 03/04/2026*
