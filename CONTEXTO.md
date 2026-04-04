# Contexto del Proyecto - Telemedicina

## Estado de la Sesión

**Última sesión**: 03/04/2026
**Directorio de trabajo**: D:\hipocrates
**Estado actual**: Sistema completo funcionando - Video P2P, grabación, transcripción, FHIR, persistencia PostgreSQL

---

## Resumen del Proyecto

Plataforma de telemedicina con:
- **Videoconsultas P2P** en tiempo real (PeerJS - WebRTC sin servidor de medios)
- **Grabación automática de audio** de cada consulta (MediaRecorder)
- **Transcripción automática** con Whisper Docker (`onerahmet/openai-whisper-asr-webservice`)
- **Extracción FHIR completa** - 4 tipos de entidades: Conditions, Medications, Observations, Procedures
- **Persistencia en PostgreSQL** - Consultas, transcripciones y grabaciones en base de datos
- **Revisión de transcripciones** - Flujo de aprobación/corrección por el doctor
- **Seguridad HIPAA** - JWT, RBAC, cifrado
- Frontend Next.js 14, Backend FastAPI

---

## Credenciales de Acceso

| Email | Rol | Contraseña |
|-------|-----|------------|
| doctor@test.com | doctor | password123 |
| patient@test.com | patient | password123 |

---

## Credenciales PostgreSQL

| Parámetro | Valor |
|-----------|-------|
| Host | localhost |
| Puerto | 5433 |
| Usuario | telemedicina |
| Contraseña | 6cc4fe60b2f494cb8ebc2b23300942b4 |
| Base de datos | telemedicina |
| Tablas | consultations, transcriptions, recordings |

---

## Credenciales MinIO

| Parámetro | Valor |
|-----------|-------|
| URL | http://localhost:9000 |
| Usuario | minioadmin |
| Contraseña | 51820dacc70cc90c931125cca6274571 |
| Bucket | recordings |
| Estado | ⚠️ SignatureDoesNotMatch - se usa fallback local |

---

## Credenciales Whisper Docker

| Parámetro | Valor |
|-----------|-------|
| Imagen | onerahmet/openai-whisper-asr-webservice:latest |
| Modelo | base (español) |
| Puerto externo | 9002 |
| Puerto interno | 9000 |
| Engine | openai_whisper |

---

## Rutas del Frontend

| Ruta | Descripción | Estado |
|------|-------------|--------|
| / | Página principal | ✅ |
| /auth/signin | Login | ✅ |
| /dashboard | Dashboard del usuario | ✅ |
| /consultations | Lista de consultas | ✅ |
| /consultations/new | Crear nueva consulta | ✅ |
| /recordings | Lista y descarga grabaciones | ✅ |
| /transcriptions | Lista y revisión de transcripciones | ✅ |
| /fhir | Visualización de entidades FHIR | ✅ |
| /room/[roomName] | Sala de videollamada (PeerJS) | ✅ |

---

## Endpoints API

### Autenticación
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | /api/v1/auth/login | Iniciar sesión (form-data: username, password) | No |
| POST | /api/v1/auth/register | Registrar usuario | No |
| GET | /api/v1/auth/me | Info del usuario actual | Sí |
| POST | /api/v1/auth/logout | Cerrar sesión | Sí |
| POST | /api/v1/auth/refresh | Refrescar token | Sí |

### Consultas
| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| GET | /api/v1/consultations/ | Listar consultas | Cualquiera |
| POST | /api/v1/consultations/ | Crear consulta | doctor/admin |
| GET | /api/v1/consultations/{id} | Obtener consulta | Cualquiera |
| PATCH | /api/v1/consultations/{id}/start | Iniciar consulta | doctor |
| PATCH | /api/v1/consultations/{id}/end | Finalizar consulta | doctor |
| DELETE | /api/v1/consultations/{id} | Cancelar consulta | doctor/admin |

### Grabaciones
| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | /api/v1/recordings/ | Subir grabación de audio | Sí |
| GET | /api/v1/recordings/list-all | Listar todas las grabaciones | Sí |
| GET | /api/v1/recordings/{consultation_id} | Listar grabaciones de una consulta | Sí |
| GET | /api/v1/recordings/{consultation_id}/{file_name} | Descargar grabación | Sí |

### IA / Transcripción / FHIR
| Método | Endpoint | Descripción | Rol |
|--------|----------|-------------|-----|
| POST | /api/v1/ia/transcribe | Transcribir audio con Whisper | doctor/admin |
| POST | /api/v1/ia/extract-fhir | Extraer entidades FHIR | doctor/admin |
| GET | /api/v1/ia/fhir/{consultation_id} | Obtener bundle FHIR de consulta | Cualquiera |
| GET | /api/v1/ia/transcriptions/{consultation_id} | Obtener transcripción | Cualquiera |
| GET | /api/v1/ia/pending-review | Listar transcripciones pendientes | doctor |
| POST | /api/v1/ia/{consultation_id}/review | Aprobar/rechazar transcripción | doctor |

### Utilidades
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /health | Estado del backend |
| GET | / | Info del API |

---

## Estado de Servicios

| Servicio | Puerto | Estado | Notas |
|----------|--------|--------|-------|
| PostgreSQL | 5433 | ✅ Corriendo | Persistencia principal |
| Redis | 6379 | ✅ Corriendo | Cache/colas |
| MinIO | 9000-9001 | ✅ Corriendo | ⚠️ Fallback local activo |
| Whisper | 9002 | ✅ Corriendo | Transcripción |
| Caddy | 80/443 | ✅ Corriendo | Reverse proxy |
| LiveKit | 7880 | ⏸️ Corriendo | No usado |
| CoTURN | 3478 | ⏸️ Corriendo | No usado |
| Backend FastAPI | 8000 | Manual | uvicorn |
| Frontend Next.js | 3000 | Manual | npm run start |

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

**Problema**: Los servicios públicos de Jitsi (`meet.jit.si`, `8x8.vc`) requieren login de Google/GitHub.

**Intentos**:
1. Iframe embebido → error de cookies de terceros
2. API externa (`external_api.js`) → error de parseo de JSON
3. Ventana nueva (`window.open`) → solicita verificación de cuenta Google
4. Todos descartados

### 3. Implementación de PeerJS (Solución Final)

**Solución**: PeerJS - WebRTC peer-to-peer con servidor de señalización gratuito.

**Ventajas**:
- No requiere cuenta, API key, ni login
- Conexión directa entre navegadores (P2P)
- Sin problemas de cookies de terceros
- Sin restricciones de iframe

**Archivos**:
- `frontend/src/components/video/VideoRoom.tsx` - Componente principal
- `frontend/src/app/room/[roomName]/page.tsx` - Página de sala

**Cómo funciona**:
1. Peer ID: `telemedicina-{roomName}-{userIdentity}-{timestamp}`
2. Descubrimiento vía `localStorage` con polling cada 3s
3. Conexión P2P directa para video/audio

### 4. Corrección de Roles en Autenticación

**Problema**: Login siempre asignaba rol "patient" → Error 403 al crear consultas.

**Solución**: Detección de rol por email en `backend/src/routers/auth.py`:
- `doctor@test.com` → doctor
- `admin@test.com` → admin
- `patient@test.com` → patient

### 5. Grabación de Audio

**Frontend** (`VideoRoom.tsx`):
- `MediaRecorder` con formato `audio/webm;codecs=opus`
- Indicador rojo "Grabando" con cronómetro
- Upload al backend al salir

**Backend** (`recordings.py`):
- Upload con fallback local si MinIO falla
- Transcripción automática en hilo separado

### 6. Transcripción con Whisper Docker

**Problema anterior**: whispercpp incompatible con Python 3.13.

**Solución**: Contenedor `onerahmet/openai-whisper-asr-webservice`.

**Flujo**:
1. Frontend sube audio webm
2. Backend convierte a WAV con ffmpeg (16kHz, mono)
3. Envía a Whisper vía HTTP POST
4. Guarda transcripción en DB + archivo JSON

### 7. Extracción FHIR Completa

**Diccionarios médicos**:
- **SNOMED CT**: 25+ síntomas/condiciones (cefalea, fiebre, tos, dolor abdominal, etc.)
- **RxNorm**: 20+ medicamentos (ibuprofeno, paracetamol, amoxicilina, etc.)
- **LOINC**: 11 signos vitales (presión arterial, frecuencia cardíaca, temperatura, etc.)
- **SNOMED Procedures**: 14 procedimientos (vacunación, electrocardiograma, etc.)

**Tipos de recursos FHIR generados**:
- `Encounter` - Consulta virtual
- `Condition` - Diagnósticos con código SNOMED
- `MedicationRequest` - Medicamentos con código RxNorm y dosis
- `Observation` - Signos vitales con código LOINC y valores
- `Procedure` - Procedimientos con código SNOMED

**Validación**: Cada bundle se valida contra reglas FHIR básicas.

### 8. Persistencia en PostgreSQL

**Modelos** (`backend/src/models/consultation.py`):
- `Consultation` - id, patient_id, practitioner_id, room_name, status, scheduled_at, started_at, ended_at, duration_minutes, notes
- `Transcription` - consultation_id (FK), transcription_text, language, segments, fhir_bundle, fhir_entities, fhir_valid, reviewed, approved, corrections
- `Recording` - consultation_id (FK), file_name, file_path, file_size, duration_seconds, storage_type

**Seed script** (`backend/scripts/seed_db.py`):
- Importa datos existentes de archivos JSON a PostgreSQL
- Crea tablas automáticamente al iniciar el backend

### 9. Frontend FHIR

**Página `/fhir`**:
- Busca por ID de consulta
- Muestra entidades por categoría con colores:
  - 🔴 Diagnósticos (Condition)
  - 🔵 Medicamentos (MedicationRequest)
  - 🟢 Signos Vitales (Observation)
  - 🟣 Procedimientos (Procedure)
- Cada entidad muestra nombre, código y sistema de codificación

---

## Cómo Iniciar los Servicios

### 1. Verificar Docker
```powershell
docker ps
```

### 2. Forzar reinicio del backend
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

### 5. Seed Database (si es necesario)
```powershell
cd D:\hipocrates\backend
python scripts/seed_db.py
```

---

## Flujo de Prueba Completo

1. Abrir http://localhost:3000
2. Login: `doctor@test.com` / `password123`
3. Ir a "Nueva Consulta" → seleccionar paciente y fecha → crear
4. Ir a "Mis Consultas" → click "Unirse" en una consulta
5. Ingresar nombre e identidad → "Unirse a la consulta"
6. Se inicia la videollamada con PeerJS + grabación automática
7. Abrir otra pestaña, entrar como `patient@test.com` a la misma consulta
8. Al finalizar, click "Salir" → grabación se sube + transcripción automática
9. Ver grabaciones en `/recordings`
10. Ver transcripciones en `/transcriptions` (aprobar/rechazar)
11. Ver entidades FHIR en `/fhir` (ingresar ID de consulta)

---

## Estructura Completa de Archivos

### Frontend
```
frontend/src/
├── app/
│   ├── api/
│   │   └── consultations/[roomName]/peers/route.ts  # Peer discovery API
│   ├── auth/
│   │   ├── signin/page.tsx       # Login con NextAuth
│   │   └── error/page.tsx        # Página de error auth
│   ├── consultations/
│   │   ├── page.tsx              # Lista de consultas + botones navegación
│   │   └── new/page.tsx          # Formulario crear consulta
│   ├── dashboard/page.tsx        # Dashboard
│   ├── fhir/page.tsx             # NUEVO - Visualización FHIR
│   ├── recordings/page.tsx       # Lista/descarga grabaciones
│   ├── room/[roomName]/page.tsx  # Sala de videollamada
│   ├── transcriptions/page.tsx   # Lista/revisión transcripciones
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home
│   ├── providers.tsx             # Session provider
│   └── globals.css
├── components/
│   ├── ai/
│   │   └── ReviewDashboard.tsx   # Dashboard revisión IA
│   ├── consultation/             # Componentes de consulta
│   ├── layout/
│   │   └── Header.tsx            # Header con navegación
│   ├── ui/
│   │   ├── Button.tsx            # Botón reutilizable
│   │   ├── Card.tsx              # Card reutilizable
│   │   └── Input.tsx             # Input reutilizable
│   └── video/
│       ├── VideoRoom.tsx         # PeerJS + grabación + transcripción
│       ├── Controls.tsx          # Controles (mic, cámara, salir)
│       ├── ParticipantTile.tsx   # Tile de participante
│       └── JitsiRoom.tsx         # Legacy (no usado)
├── hooks/
│   ├── useAuth.tsx               # Hook autenticación
│   ├── useJitsi.ts               # Legacy (no usado)
│   └── useLiveKit.ts             # Legacy (no usado)
├── lib/
│   ├── auth.ts                   # NextAuth config
│   ├── api.ts                    # Cliente API
│   └── fetchApi.ts               # Fetch wrapper
└── types/
    └── next-auth.d.ts            # Tipos NextAuth
```

### Backend
```
backend/
├── src/
│   ├── main.py                   # FastAPI app + CORS + lifespan (create tables)
│   ├── core/
│   │   ├── config.py             # Settings (DB, MinIO, JWT, Whisper)
│   │   └── security.py           # JWT, require_role, get_current_user
│   ├── models/
│   │   ├── database.py           # SQLAlchemy engine, session, Base
│   │   ├── user.py               # Modelo User
│   │   └── consultation.py       # Consultation, Transcription, Recording
│   ├── routers/
│   │   ├── auth.py               # Login con detección de rol
│   │   ├── consultations.py      # CRUD consultas (PostgreSQL)
│   │   ├── recordings.py         # Upload + transcripción auto + DB
│   │   ├── ia.py                 # Transcripción, FHIR, review
│   │   ├── livekit.py            # Legacy (no usado)
│   │   ├── fhir.py               # FHIR endpoints
│   │   └── webhooks.py           # Webhooks
│   ├── services/
│   │   ├── minio_client.py       # Cliente MinIO (lazy loading)
│   │   ├── whisper_transcriber.py # Transcripción vía Docker
│   │   ├── fhir_mapper.py        # Mapeo a FHIR (SNOMED, RxNorm, LOINC)
│   │   └── livekit_client.py     # Legacy (no usado)
│   ├── middleware/                # Auditoría HIPAA
│   ├── models/                    # Modelos Pydantic
│   └── queue/                     # Colas Redis
├── recordings/                    # Grabaciones locales (fallback)
│   └── {consultation_id}/
│       └── {uuid}_{filename}.webm
├── transcriptions/                # Transcripciones JSON (backup)
│   └── {consultation_id}.json
├── scripts/
│   ├── seed_db.py                # Seed database desde JSON existentes
│   └── test_livekit_token.py     # Test token LiveKit
├── tests/                         # Tests unitarios
└── requirements.txt
```

### Docker
```
docker-compose.yml                 # PostgreSQL, Redis, MinIO, Whisper, Caddy, LiveKit, CoTURN
turnserver.conf                    # CoTURN (corregido)
.env                               # Variables de entorno
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

### Transcripción (Whisper Docker)
- Imagen: `onerahmet/openai-whisper-asr-webservice:latest`
- Modelo: `base` (español)
- Puerto: 9002 (externo) → 9000 (interno)
- Backend convierte webm → wav con ffmpeg (16kHz, mono, pcm_s16le)
- Envía audio vía HTTP POST a `http://whisper:9000/asr`
- Transcripción en hilo separado (no bloquea respuesta)
- Timeout: 300 segundos

### Extracción FHIR
- **SNOMED CT**: 25+ condiciones (cefalea, fiebre, tos, dolor abdominal, vacunación, etc.)
- **RxNorm**: 20+ medicamentos (ibuprofeno, paracetamol, amoxicilina, metformina, etc.)
- **LOINC**: 11 signos vitales (presión arterial, frecuencia cardíaca, temperatura, etc.)
- **SNOMED Procedures**: 14 procedimientos (vacunación, electrocardiograma, ecografía, etc.)
- Regex para extraer dosis de medicamentos
- Regex para extraer valores de signos vitales
- Validación FHIR básica (resourceType, required fields)

### Base de Datos (PostgreSQL)
- **Tablas**: consultations, transcriptions, recordings
- **Relaciones**: Transcription 1:1 con Consultation, Recording N:1 con Consultation
- **Creación automática**: `Base.metadata.create_all()` en lifespan del backend
- **Seed script**: Importa datos de JSON existentes a PostgreSQL

### Autenticación
- NextAuth con estrategia JWT
- Token expira en 15 minutos
- Roles detectados por email en backend
- `session.accessToken` = JWT del backend

### MinIO
- Bucket `recordings` creado manualmente
- Acceso web: http://localhost:9000
- ⚠️ SignatureDoesNotMatch - las grabaciones se guardan en disco local como fallback

---

## Pendientes

1. **MinIO SignatureDoesNotMatch** - Corregir credenciales para almacenamiento S3
2. **Mejorar calidad de transcripción** - Usar modelo `medium` o `large` de Whisper
3. **Dashboard médico del paciente** - Historial consolidado de consultas
4. **Generar reporte PDF** - Exportar consulta completa como documento clínico
5. **Notificaciones** - Alertar al paciente cuando el doctor inicia la consulta
6. **Persistencia de usuarios** - Guardar usuarios en PostgreSQL en vez de hardcodeados

---

## Problemas Conocidos

1. **MinIO SignatureDoesNotMatch** - Credenciales no coinciden, fallback a disco local funciona
2. **LiveKit y CoTURN** corren en Docker pero no se usan
3. **Servicio Jitsi local** en docker-compose no configurado
4. **Se requiere internet** para PeerJS (señalización) y Whisper (contenedor Docker)
5. **Calidad de transcripción** - Modelo `base` puede distorsionar nombres de medicamentos

---

*Actualizado: 03/04/2026*
