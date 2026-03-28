# Telemedicina LiveKit

Plataforma de telemedicina con videoconsultas en tiempo real, transcripción automática e integración FHIR.

## Características

- **Videoconsultas en Tiempo Real**: WebRTC con LiveKit
- **Transcripción Automática**: Whisper para STT en español
- **Extracción FHIR**: Entidades clínicas automáticas
- **Seguridad HIPAA**: Cifrado, auditoría, RBAC
- **Accesibilidad WCAG 2.1 AA**

## Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL│
│  Next.js    │     │   FastAPI   │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │             ┌─────┴─────┐            │
       │             │           │            │
       ▼             ▼           ▼            ▼
┌──────────┐   ┌────────┐  ┌────────┐   ┌────────┐
│  LiveKit  │   │ Redis  │  │  MinIO │   │ OpenEMR│
│  (WebRTC) │   │  Queue │  │Storage │   │  FHIR  │
└──────────┘   └────────┘  └────────┘   └────────┘
```

## Inicio Rápido

### Desarrollo Local

```bash
# 1. Clonar repositorio
git clone https://github.com/telemedicina/telemedicina-livekit.git
cd telemedicina-livekit

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Iniciar servicios
docker compose up -d

# 4. Instalar dependencias backend
cd backend
pip install -r requirements.txt

# 5. Instalar dependencias frontend
cd ../frontend
npm install

# 6. Iniciar desarrollo
# Backend: uvicorn src.main:app --reload
# Frontend: npm run dev
```

### Producción

Ver [docs/deployment.md](docs/deployment.md)

## Estructura del Proyecto

```
telemedicina-livekit/
├── backend/              # API FastAPI
│   └── src/
│       ├── routers/      # Endpoints
│       ├── models/       # Modelos DB
│       ├── services/     # Lógica de negocio
│       └── middleware/   # Auditoría
├── frontend/             # Next.js 14
│   └── src/
│       ├── components/   # Componentes React
│       ├── hooks/       # Custom hooks
│       └── lib/         # Utilidades
├── agents/              # Workers IA
├── charts/              # Helm charts
├── k8s/                 # Kubernetes manifests
├── scripts/             # Scripts automation
├── monitoring/           # Prometheus + Grafana
├── docs/                # Documentación
└── docker-compose.yml   # Desarrollo local
```

## Configuración OpenCode

El proyecto incluye configuración para ejecución con OpenCode:

```bash
# Iniciar sesión
opencode

# Ejecutar fase específica
@infra-setup Configurar infraestructura
@backend-api Desarrollar backend
@frontend-ui Desarrollar frontend
@ai-pipeline Configurar IA
@security-audit Auditoría de seguridad
```

Ver [.opencode/](.opencode/) para configuración detallada.

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/v1/auth/login | Autenticación |
| POST | /api/v1/auth/register | Registro |
| GET | /fhir/Patient | Listar pacientes |
| POST | /fhir/Encounter | Crear encuentro |
| GET | /api/v1/consultations | Listar consultas |
| POST | /api/v1/ia/transcribe | Transcribir audio |
| POST | /api/v1/ia/extract-fhir | Extraer entidades FHIR |

## Tecnologías

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, LiveKit SDK
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **IA**: Whisper, LLM para extracción FHIR
- **Infra**: Docker, Kubernetes, Helm
- **Monitoreo**: Prometheus, Grafana

## Seguridad

- TLS 1.3 para todas las comunicaciones
- JWT con expiración de 15 minutos
- Cifrado AES-256 en reposo
- Logs de auditoría HIPAA
- RBAC con roles: admin, doctor, patient

## Contribuir

1. Fork el repositorio
2. Crear rama (`git checkout -b feature/amazing`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Crear Pull Request

## Licencia

MIT License - voir [LICENSE](LICENSE) pour plus de détails.

---

**Nota**: Este proyecto es un boilerplate/template para proyectos de telemedicina. Antes de usar en producción, asegurar cumplimiento con regulaciones locales de salud.
