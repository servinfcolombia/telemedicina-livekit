# DOCUMENTACIÓN TÉCNICA - HIPÓCRATES
## Plataforma de Telemedicina con Videoconsultas, Transcripción IA y Extracción FHIR

**Última actualización**: 07/04/2026  
**Estado**: ✅ Producción  
**Docker**: 6 servicios activos

---

## 1. ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USUARIO                                         │
│                    (Médico o Paciente)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js 14)                              │
│                        Puerto: 3000 (HTTP)                                   │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │    Login     │  │ Consultas    │  │ Grabaciones  │  │   Dashboard  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │        API REST (FastAPI)      │
                    │         Puerto: 8000          │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────────────┐
│  PostgreSQL   │         │    Redis      │         │       MinIO           │
│ Puerto: 5433  │         │ Puerto: 6379  │         │ Puerto: 9000-9001    │
│ (Relacional)  │         │   (Cache)     │         │   (Almacenamiento)    │
└───────────────┘         └───────────────┘         └───────────────────────┘
        │                                                   │
        │                                                   ▼
        │                                       ┌───────────────────────┐
        │                                       │   Whisper Docker      │
        │                                       │   Puerto: 9002→9000   │
        │                                       │   (Transcripción IA)  │
        │                                       └───────────────────────┘
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         DATOS CLÍNICOS FHIR                                   │
│         Condiciones │ Medicamentos │ Observaciones │ Procedimientos            │
│         SNOMED CT   │   RxNorm    │    LOINC     │    SNOMED               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. FLUJO DE PROCESO

### 2.1 Flujo Completo de una Videoconsulta

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ETAPA 1: AUTENTICACIÓN                              │
└──────────────────────────────────────────────────────────────────────────┘

  Usuario                    Frontend                    Backend
     │                          │                          │
     │─── Login (email/pass) ──▶│                          │
     │                          │─── POST /auth/login ────▶│
     │                          │                          │──▶ Validar credenciales
     │                          │                          │──▶ Generar JWT (15 min)
     │                          │◀── Token + Refresh ─────│
     │◀── Dashboard ────────────│                          │
     │                          │                          │

  📍 DATOS: Credenciales validadas en memoria (no persistidas)

───────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                     ETAPA 2: INICIO DE CONSULTA                            │
└──────────────────────────────────────────────────────────────────────────┘

  Médico                     Frontend                    Backend
     │                          │                          │
     │─── Crear consulta ──────▶│                          │
     │                          │─── POST /consultations ─▶│
     │                          │                          │──▶ Crear Room ID
     │                          │                          │──▶ Guardar en PostgreSQL
     │◀── Room ID ─────────────│◀── Consultation ─────────│
     │                          │                          │
     │─── Unirse al room ──────▶│                          │
     │                          │─── GET /consultations ──▶│
     │◀── Video Room ──────────│◀── Lista ────────────────│

  📍 DATOS: consultation_id, patient_id, doctor_id, status, timestamps
     📦 TABLA: consultations (PostgreSQL)

───────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                   ETAPA 3: VIDEOCONSULTA P2P (PeerJS)                    │
└──────────────────────────────────────────────────────────────────────────┘

  Paciente                   PeerJS                       Médico
     │                          │                          │
     │─── Iniciar Peer ────────▶│                          │
     │                          │◀── Peer ID ──────────────│
     │◀── Compartir Peer ID ────┤                          │
     │                          │                          │─── Conectar P2P ────┤
     │◀────────────────────────────────── Stream Video ────▶│
     │◀────────────────────────────────── Stream Video ────▶│

  📍 DATOS: Streams de audio/video en memoria (no persistidos)

───────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                     ETAPA 4: GRABACIÓN DE AUDIO                           │
└──────────────────────────────────────────────────────────────────────────┘

  Navegador                   Frontend                    MinIO
     │                          │                          │
     │─── MediaRecorder.start ──▶│                          │
     │◀── Blob chunks ──────────││                          │
     │                          │                          │
     │─── Detener grab. ───────▶│                          │
     │─── Enviar .webm ────────▶│                          │
     │                          │─── POST /recordings ────▶│
     │                          │                          │──▶ Guardar en bucket
     │                          │                          │
     │                          │◀── 201 Created ──────────│
     │                          │                          │

  📍 DATOS: Audio .webm
     📦 ALMACENAMIENTO: MinIO (bucket: telemedicina-recordings)

───────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                    ETAPA 5: TRANSCRIPCIÓN (Whisper)                       │
└──────────────────────────────────────────────────────────────────────────┘

  Backend                     Whisper Docker              PostgreSQL
     │                          │                          │
     │─── Leer .webm ──────────▶│                          │
     │                          │─── Convertir a WAV ──────│
     │                          │─── POST /asr ───────────▶│
     │                          │◀── Texto transcrito ─────│
     │                          │                          │
     │─── Guardar transcripción ───────────────────────────▶│
     │                          │                          │──▶ INSERT transcriptions

  📍 DATOS: transcription_text, language, segments
     📦 TABLA: transcriptions (PostgreSQL)

───────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                   ETAPA 6: EXTRACCIÓN FHIR                                │
└──────────────────────────────────────────────────────────────────────────┘

  Backend                     FHIR Mapper                 Terminología
     │                          │                          │
     │─── Extraer entidades ────▶│                          │
     │                          │─── Analizar texto ───────│
     │                          │                          │
     │                          │─── Búsqueda SNOMED ──────▶│ (médicamentos, síntomas)
     │                          │─── Búsqueda RxNorm ─────▶│ (medicamentos)
     │                          │─── Búsqueda LOINC ──────▶│ (observaciones)
     │                          │                          │
     │─── Crear FHIR Bundle ───▶│                          │
     │                          │──▶ Condition (SNOMED CT)  │
     │                          │──▶ MedicationStatement    │
     │                          │──▶ Observation (LOINC)   │
     │                          │──▶ Procedure (SNOMED)    │
     │                          │                          │
     │─── Guardar Bundle ────────────────────────────────▶│
     │                          │                          │──▶ UPDATE transcriptions

  📍 DATOS: FHIR Bundle JSON con recursos codificados
     📦 TABLA: transcriptions.fhir_bundle, transcriptions.fhir_entities

───────────────────────────────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────────┐
│                     ETAPA 7: VISUALIZACIÓN FHIR                           │
└──────────────────────────────────────────────────────────────────────────┘

  Médico                     Frontend                    Backend
     │                          │                          │
     │─── Ver transcripción ────▶│                          │
     │                          │─── GET /transcriptions ──▶│
     │                          │◀── Transcripción + FHIR ─│
     │◀── Mostrar entidades ────│                          │
     │                          │                          │
     │─── Revisar/corrección ──▶│                          │
     │                          │─── PATCH /transcriptions ─▶│
     │                          │                          │──▶ UPDATE reviewed=true
     │                          │                          │──▶ Guardar correcciones

  📍 DATOS: Correcciones del médico
     📦 TABLA: transcriptions.reviewed, transcriptions.corrections
```

---

## 3. APLICACIONES Y SERVICIOS

### 3.1 Servicios Docker

| Servicio | Imagen | Puerto | Descripción | Dependencias |
|----------|--------|--------|-------------|---------------|
| **frontend** | hipocrates-frontend | 3000 | Next.js 14 App Router | backend (API) |
| **backend** | hipocrates-backend | 8000 | FastAPI REST API | postgres, redis, minio, whisper |
| **postgres** | postgres:15-alpine | 5433→5432 | Base de datos relacional | - |
| **redis** | redis:7-alpine | 6379 | Cache de sesiones | - |
| **minio** | minio/minio:latest | 9000-9001 | Object storage (S3 compatible) | - |
| **whisper** | onerahmet/openai-whisper-asr-webservice | 9002→9000 | Whisper API REST | - |

### 3.2 Tecnologías por Capa

**Frontend (Presentacion)**
- Next.js 14 (App Router)
- React 18
- TailwindCSS
- Heroicons
- PeerJS (WebRTC P2P)
- MediaRecorder API

**Backend (Lógica de Negocio)**
- FastAPI (Python 3.13)
- SQLAlchemy 2.0 (ORM)
- Pydantic v2 (Validación)
- python-jose (JWT)
- bcrypt (Contraseñas)

**Inteligencia Artificial**
- Whisper (OpenAI) - Transcripción
- FHIR Mapper - Extracción de entidades médicas
- Terminologías: SNOMED CT, RxNorm, LOINC

**Almacenamiento**
- PostgreSQL 15 - Datos estructurados
- MinIO - Archivos binarios (audio, videos)
- Redis - Cache de sesiones

---

## 4. ALMACENAMIENTO DE DATOS

### 4.1 PostgreSQL - Datos Estructurados

```sql
-- Consultas médicas
consultations (
    id              VARCHAR PRIMARY KEY,
    room_name       VARCHAR UNIQUE,
    patient_id      VARCHAR,
    doctor_id       VARCHAR,
    patient_name    VARCHAR,
    reason          TEXT,
    status          VARCHAR,  -- 'scheduled', 'in_progress', 'completed'
    started_at      TIMESTAMP,
    ended_at        TIMESTAMP,
    created_by      VARCHAR,
    created_at      TIMESTAMP
)

-- Grabaciones de audio
recordings (
    id              VARCHAR PRIMARY KEY,
    consultation_id VARCHAR REFERENCES consultations(id),
    file_name       VARCHAR,
    file_path       VARCHAR,  -- Ruta en MinIO o local
    file_size       INTEGER,
    duration_seconds INTEGER,
    storage_type    VARCHAR,  -- 'minio' o 'local'
    created_by      VARCHAR,
    created_at      TIMESTAMP
)

-- Transcripciones y FHIR
transcriptions (
    id                VARCHAR PRIMARY KEY,
    consultation_id   VARCHAR REFERENCES consultations(id) UNIQUE,
    transcription_text TEXT,
    language          VARCHAR,
    segments          TEXT,  -- JSON con segmentos
    fhir_bundle       TEXT,  -- JSON FHIR Bundle
    fhir_entities     TEXT,  -- JSON entidades extraídas
    fhir_valid        BOOLEAN,
    reviewed          BOOLEAN,
    approved          BOOLEAN,
    corrections       TEXT,  -- Correcciones del médico
    reviewed_by       VARCHAR,
    reviewed_at       TIMESTAMP,
    created_by        VARCHAR,
    created_at        TIMESTAMP,
    updated_at        TIMESTAMP
)
```

### 4.2 MinIO - Archivos Binarios

```
Bucket: telemedicina-recordings
└── {consultation_id}/
    ├── {uuid}_consulta_{consultation_id}.webm    -- Grabación original
    ├── {uuid}_consulta_{consultation_id}.wav     -- Audio convertido
    └── thumbnails/                                -- (futuro)
```

### 4.3 Redis - Cache

```
Key: session:{user_id}
Value: JWT tokens, datos de sesión
TTL: 3600 segundos (1 hora)

Key: whisper:task:{consultation_id}
Value: Estado de transcripción
TTL: 3600 segundos
```

### 4.4 Resumen de Almacenamiento por Etapa

| Etapa | Tipo de Dato | Almacenamiento | Formato |
|-------|--------------|----------------|---------|
| Autenticación | Credenciales | Backend (memoria) | JWT |
| Consulta | Metadatos | PostgreSQL | JSON |
| Video | Streams | Memoria (P2P) | WebRTC |
| Grabación | Audio | MinIO | .webm |
| Transcripción | Texto | PostgreSQL | JSON |
| FHIR | Clínico | PostgreSQL | FHIR R4 JSON |
| Cache | Sesiones | Redis | Key-Value |

---

## 5. ENDPOINTS DE LA API

### 5.1 Autenticación
```
POST /api/v1/auth/login      - Login (username/password → JWT)
POST /api/v1/auth/register   - Registro de usuarios
POST /api/v1/auth/refresh    - Refrescar token
POST /api/v1/auth/logout     - Cerrar sesión
GET  /api/v1/auth/me         - Usuario actual
```

### 5.2 Consultas
```
GET  /api/v1/consultations/           - Lista de consultas
POST /api/v1/consultations/           - Crear consulta
GET  /api/v1/consultations/{id}       - Detalle de consulta
PUT  /api/v1/consultations/{id}       - Actualizar consulta
DELETE /api/v1/consultations/{id}      - Eliminar consulta
```

### 5.3 Grabaciones
```
POST /api/v1/recordings/              - Subir grabación
GET  /api/v1/recordings/list-all      - Lista todas las grabaciones
GET  /api/v1/recordings/{consultation_id} - Grabaciones por consulta
GET  /api/v1/recordings/{consultation_id}/{filename} - Descargar
DELETE /api/v1/recordings/{id}        - Eliminar grabación
```

### 5.4 Transcripción y FHIR
```
GET  /api/v1/ia/transcriptions/{consultation_id} - Transcripción + FHIR
POST /api/v1/ia/transcribe/{consultation_id}     - Re-transcribir
GET  /api/v1/ia/fhir/{consultation_id}           - Solo FHIR Bundle
PUT  /api/v1/ia/transcriptions/{id}/review       - Revisar/corrección
```

---

## 6. CONFIGURACIÓN DE REDES

### 6.1 Red Docker
```
Network: hipocrates_telemedicina (bridge)
```

### 6.2 Comunicación Interna
```
frontend  → backend:     http://telemedicina-backend:8000
backend   → postgres:    postgresql://telemedicina-postgres:5432
backend   → redis:       redis://telemedicina-redis:6379
backend   → minio:       http://telemedicina-minio:9000
backend   → whisper:     http://telemedicina-whisper:9000
```

### 6.3 Exposición Externa
```
localhost:3000  → frontend  (HTTP)
localhost:8000  → backend   (HTTP)
localhost:5433  → postgres  (PostgreSQL)
localhost:6379  → redis     (Redis CLI)
localhost:9000  → minio     (API S3)
localhost:9001  → minio     (Console)
localhost:9002  → whisper   (ASR API)
```

---

## 7. VARIABLES DE ENTORNO

### Backend (.env)
```env
DATABASE_URL=postgresql+psycopg://telemedicina:password@postgres:5432/telemedicina
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=password
MINIO_BUCKET_NAME=telemedicina-recordings
WHISPER_SERVER_URL=http://whisper:9000/asr
SECRET_KEY=jwt-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:3000
INTERNAL_API_URL=http://telemedicina-backend:8000
NEXTAUTH_SECRET=nextauth-secret-change-in-production
NEXTAUTH_URL=http://localhost:3000
```

---

## 8. INSTALACIÓN Y DESPLIEGUE

### 8.1 Requisitos
- Docker Engine 20.10+
- Docker Compose 2.0+
- Puerto 3000, 8000, 5433, 6379, 9000-9002 disponibles

### 8.2 Despliegue Rápido
```bash
# Clonar repositorio
git clone https://github.com/servinfcolombia/telemedicina-livekit.git
cd telemedicina-livekit

# Configurar variables de entorno
cp .env.example .env
# Editar .env según sea necesario

# Iniciar todos los servicios
docker compose up -d --build

# Verificar estado
docker compose ps
```

### 8.3 Verificación Post-Instalación
```bash
# Estado de servicios
docker compose ps

# Logs del backend
docker compose logs -f backend

# Prueba de login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor@test.com&password=password123"
```

---

## 9. CREDENCIALES DEFAULT

| Servicio | Usuario | Contraseña | URL |
|----------|---------|------------|-----|
| Frontend | doctor@test.com | password123 | http://localhost:3000 |
| Frontend | admin@test.com | password123 | http://localhost:3000 |
| Frontend | patient@test.com | password123 | http://localhost:3000 |
| PostgreSQL | telemedicina | (generado) | localhost:5433 |
| MinIO Console | minioadmin | (generado) | http://localhost:9001 |

---

## 10. ESTRUCTURA DE ARCHIVOS

```
hipocrates/
├── backend/
│   ├── src/
│   │   ├── routers/           # Endpoints API
│   │   │   ├── auth.py
│   │   │   ├── consultations.py
│   │   │   ├── recordings.py
│   │   │   └── ia.py
│   │   ├── services/         # Lógica de negocio
│   │   │   ├── whisper_transcriber.py
│   │   │   ├── fhir_mapper.py
│   │   │   └── minio_client.py
│   │   ├── models/           # ORM
│   │   │   ├── consultation.py
│   │   │   └── database.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   │   ├── consultations/
│   │   │   ├── recordings/
│   │   │   ├── transcriptions/
│   │   │   ├── fhir/
│   │   │   ├── room/[roomName]/
│   │   │   └── auth/signin/
│   │   ├── components/
│   │   │   └── video/VideoRoom.tsx
│   │   └── lib/
│   │       └── auth.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env
├── CONTEXTO.md
└── README.md
```

---

## 11. GLOSARIO

| Término | Descripción |
|---------|-------------|
| **FHIR** | Fast Healthcare Interoperability Resources - Estándar para intercambio de información clínica |
| **SNOMED CT** | Systematized Nomenclature of Medicine - Terminología clínica global |
| **RxNorm** | Normalized naming system for drugs - Terminología de medicamentos |
| **LOINC** | Logical Observation Identifiers Names and Codes - Terminología de observaciones |
| **PeerJS** | Biblioteca JavaScript para WebRTC P2P simplificado |
| **MinIO** | Object storage compatible con S3 API |
| **Whisper** | Modelo de OpenAI para transcripción de audio a texto |

---

## 12. CONTACTO Y SOPORTE

- **Repositorio**: https://github.com/servinfcolombia/telemedicina-livekit
- **Documentación API**: http://localhost:8000/docs (Swagger UI)
- **MinIO Console**: http://localhost:9001
