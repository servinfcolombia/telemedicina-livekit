# Telemedicina LiveKit - Configuración OpenCode

## Estructura

```
.opencode/
├── agents/              # Subagentes especializados
│   ├── infra-setup.md
│   ├── backend-api.md
│   ├── frontend-ui.md
│   ├── ai-pipeline.md
│   └── security-audit.md
├── prompts/            # Prompts personalizados
│   ├── fhir-extraction.txt
│   ├── livekit-config.txt
│   └── hipaa-checklist.txt
├── workflows/          # Flujos de ejecución por fase
│   ├── phase-infra.json
│   ├── phase-backend.json
│   ├── phase-frontend.json
│   ├── phase-ia.json
│   └── telemedicina-main.json
├── hooks/              # Scripts de automatización
│   └── on-phase-complete.sh
├── PROGRESS.md         # Dashboard de progreso
└── opencode.json       # Configuración principal
```

## Uso

### Iniciar sesión OpenCode

```bash
cd telemedicina-livekit && opencode
```

### Ejecutar una fase específica

```bash
@infra-setup Ejecuta las tareas de phase-1-infra
@backend-api Inicia phase-2-backend
@frontend-ui Inicia phase-3-frontend
@ai-pipeline Inicia phase-4-ai
@security-audit Inicia phase-5-security
```

### Verificar progreso

```bash
cat .opencode/PROGRESS.md
```

## Fases del Proyecto

1. **Phase 0: Preparación** - Configuración inicial del proyecto
2. **Phase 1: Infraestructura** - LiveKit, Kubernetes, SSL
3. **Phase 2: Backend** - FastAPI, FHIR, autenticación
4. **Phase 3: Frontend** - Next.js, LiveKit SDK
5. **Phase 4: IA Pipeline** - Whisper, extracción FHIR
6. **Phase 5: Seguridad** - Auditoría HIPAA/WCAG
7. **Phase 6: Despliegue** - Producción y documentación

## Requisitos

- Docker y Docker Compose
- Kubernetes (K3s) o K3d
- kubectl configurado
- Node.js 18+
- Python 3.11+
- Git

## Validaciones

Cada fase incluye validaciones automáticas. Ver archivo de workflow correspondiente para detalles.
