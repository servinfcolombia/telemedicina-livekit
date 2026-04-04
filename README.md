# Telemedicina - Plataforma de Videoconsultas

Plataforma de telemedicina con videoconsultas en tiempo real (P2P), grabación automática de audio, transcripción con Whisper e integración FHIR.

## Características

- **Videoconsultas P2P**: WebRTC con PeerJS (sin servidor de medios)
- **Grabación Automática**: Audio de cada consulta se graba automáticamente
- **Transcripción Whisper**: Transcripción automática en español vía Docker
- **Extracción FHIR**: Entidades clínicas automáticas desde transcripciones
- **Revisión de Transcripciones**: Flujo de aprobación/corrección por el doctor
- **Seguridad HIPAA**: Cifrado, RBAC, tokens JWT
- **Accesibilidad WCAG 2.1 AA**

## Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL│
│  Next.js    │     │   FastAPI   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       ││                  ││                  │
       ││             ┌────┴┐            ┌────┴────┐
       ││             │     │            │         │
       ▼▼             ▼     ▼            ▼         ▼
 ┌──────────┐   ┌────────┐ ┌──────┐  ┌──────┐ ┌────────┐
 │  PeerJS  │   │ Redis  │ │MinIO │  │Whisper│ │ OpenEMR│
 │  (WebRTC)│   │  Queue │ │(S3)  │  │(Docker│ │  FHIR  │
 └──────────┘   └────────┘ └──────┘  └───────┘ └────────┘
```

## Inicio Rápido

### Desarrollo Local

```bash
# 1. Clonar repositorio
git clone https://github.com/servinfcolombia/telemedicina-livekit.git
cd telemedicina-livekit

# 2. Copiar variables de entorno
cp .env.example .env  # o crear .env manualmente

# 3. Iniciar servicios Docker (PostgreSQL, Redis, MinIO, Whisper)
docker compose up -d

# 4. Instalar dependencias backend
cd backend
pip install -r requirements.txt

# 5. Instalar dependencias frontend
cd ../frontend
npm install

# 6. Iniciar desarrollo
# Terminal 1 - Backend:
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend:
cd frontend
npm run build
npm run start
```

### Credenciales de Prueba

| Email | Rol | Contraseña |
|-------|-----|------------|
| doctor@test.com | doctor | password123 |
| patient@test.com | patient | password123 |

### Flujo de Prueba

1. Abrir http://localhost:3000
2. Login con `doctor@test.com` / `password123`
3. Crear nueva consulta o unirse a una existente
4. La videollamada inicia con grabación y transcripción automática
5. Al salir, la grabación se guarda y la transcripción se genera
6. Ver transcripciones en `/transcriptions` y grabaciones en `/recordings`

## Estructura del Proyecto

```
telemedicina-livekit/
├── backend/                        # API FastAPI
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py          # Configuración (MinIO, JWT, Whisper)
│   │   │   └── security.py        # JWT, require_role, get_current_user
│   │   ├── routers/
│   │   │   ├── auth.py            # Login con detección de rol por email
│   │   │   ├── consultations.py   # CRUD consultas (dinámico en memoria)
│   │   │   ├── fhir.py            # Endpoints FHIR
│   │   │   ├── ia.py              # Transcripción + FHIR + revisión
│   │   │   ├── livekit.py         # Legacy (no usado)
│   │   │   ├── recordings.py      # Upload/list/download grabaciones
│   │   │   └── webhooks.py        # Webhooks
│   │   ├── services/
│   │   │   ├── fhir_mapper.py     # Mapeo FHIR
│   │   │   ├── livekit_client.py  # Legacy (no usado)
│   │   │   ├── minio_client.py    # Cliente MinIO S3
│   │   │   └── whisper_transcriber.py # Transcripción vía Docker
│   │   ├── middleware/            # Auditoría HIPAA
│   │   ├── models/                # Modelos Pydantic
│   │   ├── queue/                 # Colas Redis
│   │   └── main.py                # FastAPI app
│   ├── recordings/                # Grabaciones locales (fallback MinIO)
│   ├── transcriptions/            # Transcripciones JSON
│   ├── models/                    # Modelos Whisper (no usado)
│   ├── tests/                     # Tests unitarios
│   └── requirements.txt           # Dependencias Python
│
├── frontend/                       # Next.js 14 App Router
│   └── src/
│       ├── app/
│       │   ├── api/
│       │   │   └── consultations/[roomName]/peers/ # Peer discovery
│       │   ├── auth/
│       │   │   ├── signin/page.tsx      # Login
│       │   │   └── error/page.tsx       # Error auth
│       │   ├── consultations/
│       │   │   ├── page.tsx             # Lista de consultas
│       │   │   └── new/page.tsx         # Crear consulta
│       │   ├── dashboard/page.tsx       # Dashboard
│       │   ├── recordings/page.tsx      # Lista/descarga grabaciones
│       │   ├── room/[roomName]/page.tsx # Sala de videollamada
│       │   ├── transcriptions/page.tsx  # Lista/revisión transcripciones
│       │   ├── layout.tsx               # Root layout
│       │   ├── page.tsx                 # Home
│       │   ├── providers.tsx            # Session provider
│       │   └── globals.css              # Estilos globales
│       ├── components/
│       │   ├── ai/
│       │   │   └── ReviewDashboard.tsx  # Dashboard revisión IA
│       │   ├── consultation/            # Componentes de consulta
│       │   ├── layout/
│       │   │   └── Header.tsx           # Header con navegación
│       │   ├── ui/
│       │   │   ├── Button.tsx           # Botón reutilizable
│       │   │   ├── Card.tsx             # Card reutilizable
│       │   │   └── Input.tsx            # Input reutilizable
│       │   └── video/
│       │       ├── VideoRoom.tsx        # PeerJS + grabación + transcripción
│       │       ├── Controls.tsx         # Controles (mic, cámara, salir)
│       │       ├── ParticipantTile.tsx  # Tile de participante
│       │       └── JitsiRoom.tsx        # Legacy (no usado)
│       ├── hooks/
│       │   ├── useAuth.tsx              # Hook de autenticación
│       │   ├── useJitsi.ts              # Legacy (no usado)
│       │   └── useLiveKit.ts            # Legacy (no usado)
│       ├── lib/
│       │   ├── auth.ts                  # NextAuth config
│       │   ├── api.ts                   # Cliente API
│       │   └── fetchApi.ts              # Fetch wrapper
│       └── types/
│           └── next-auth.d.ts           # Tipos NextAuth
│
├── agents/                         # Workers IA (Whisper config)
├── charts/                         # Helm charts (Kubernetes)
├── k8s/                            # Kubernetes manifests
├── monitoring/                     # Prometheus + Grafana
├── docs/                           # Documentación
├── scripts/                        # Scripts de prueba
├── docker-compose.yml              # Servicios Docker
├── turnserver.conf                 # CoTURN (no usado)
├── CONTEXTO.md                     # Documentación detallada del proyecto
└── README.md                       # Este archivo
```

## API Endpoints

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/auth/login | Iniciar sesión |
| POST | /api/v1/auth/register | Registro |

### Consultas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/v1/consultations/ | Listar consultas |
| POST | /api/v1/consultations/ | Crear consulta |
| PATCH | /api/v1/consultations/{id}/start | Iniciar consulta |
| PATCH | /api/v1/consultations/{id}/end | Finalizar consulta |

### Grabaciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/recordings/ | Subir grabación |
| GET | /api/v1/recordings/list-all | Listar todas |
| GET | /api/v1/recordings/{id}/{file} | Descargar |

### IA / Transcripción
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/ia/transcribe | Transcribir audio |
| POST | /api/v1/ia/extract-fhir | Extraer entidades FHIR |
| GET | /api/v1/ia/transcriptions/{id} | Obtener transcripción |
| POST | /api/v1/ia/{id}/review | Aprobar/rechazar |

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, PeerJS |
| **Backend** | FastAPI, Python 3.13, SQLAlchemy, httpx |
| **Video** | PeerJS (WebRTC P2P) |
| **Transcripción** | Whisper Docker (onerahmet/openai-whisper-asr-webservice) |
| **Almacenamiento** | MinIO (S3 compatible) con fallback local |
| **Base de datos** | PostgreSQL 15 |
| **Cache/Queue** | Redis |
| **Infra** | Docker, Docker Compose |

## Extracción FHIR

El sistema extrae automáticamente entidades clínicas de las transcripciones:

| Tipo | Sistema | Cantidad | Ejemplos |
|------|---------|----------|---------|
| **Condition** | SNOMED CT | 25+ | Cefalea, fiebre, tos, dolor abdominal, diarrea |
| **MedicationRequest** | RxNorm | 20+ | Ibuprofeno, paracetamol, amoxicilina, metformina |
| **Observation** | LOINC | 11 | Presión arterial, frecuencia cardíaca, temperatura |
| **Procedure** | SNOMED CT | 14+ | Vacunación, electrocardiograma, ecografía |

Cada recurso FHIR incluye codificación estándar, referencias al paciente y encuentro, y validación automática.

## Servicios Docker

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| PostgreSQL | 5433 | Base de datos |
| Redis | 6379 | Cache y colas |
| MinIO | 9000-9001 | Almacenamiento S3 |
| Whisper | 9002 | Transcripción de audio |
| Caddy | 80/443 | Reverse proxy |

> **Nota**: LiveKit y CoTURN están en docker-compose pero no se usan actualmente.

## Seguridad

- TLS 1.3 para todas las comunicaciones
- JWT con expiración de 15 minutos
- Cifrado AES-256 en reposo (MinIO)
- RBAC con roles: admin, doctor, patient
- Roles detectados por email en el backend

## Evolución del Proyecto

Este proyecto pasó por varias iteraciones de video:

1. **LiveKit** → Descartado por problemas de ICE/TURN (conexión fallida entre Docker y Windows)
2. **Jitsi Meet** → Descartado porque requiere login de Google/GitHub para crear salas
3. **PeerJS** → Solución final: WebRTC P2P sin servidor de medios, sin login requerido

La transcripción también evolucionó:

1. **whispercpp (Python)** → Incompatible con Python 3.13
2. **Web Speech API** → Solo funciona en Chrome/Edge
3. **Whisper Docker** → Solución final: contenedor independiente, funciona con cualquier navegador

## Contribuir

1. Fork el repositorio
2. Crear rama (`git checkout -b feature/amazing`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Crear Pull Request

## Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

---

**Nota**: Este proyecto es un boilerplate/template para proyectos de telemedicina. Antes de usar en producción, asegurar cumplimiento con regulaciones locales de salud (HIPAA, GDPR, etc.).

**Documentación detallada**: Ver [CONTEXTO.md](CONTEXTO.md) para información completa del historial de cambios, configuración y solución de problemas.
