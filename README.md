# HIPÓCRATES - Plataforma de Telemedicina

Sistema de videoconsultas médicas con transcripción automática y extracción de datos clínicos FHIR.

## Características

- **Videoconsultas P2P** - Comunicación directa entre médico y paciente usando PeerJS
- **Grabación automática** - Registro de audio de cada consulta
- **Transcripción IA** - Whisper para convertir audio a texto
- **Extracción FHIR** - Identificación automática de condiciones, medicamentos y observaciones
- **Docker completo** - 6 servicios desplegados con un solo comando

## Inicio Rápido

```bash
# Clonar y ejecutar
git clone https://github.com/servinfcolombia/telemedicina-livekit.git
cd telemedicina-livekit
docker compose up -d --build

# Abrir en navegador
open http://localhost:3000
```

## Credenciales de Prueba

| Rol | Email | Contraseña |
|-----|-------|------------|
| Médico | doctor@test.com | password123 |
| Paciente | patient@test.com | password123 |

## Arquitectura

```
Frontend (Next.js) ──▶ Backend (FastAPI) ──▶ PostgreSQL
                          │
                          ├──▶ MinIO (grabaciones)
                          ├──▶ Whisper (transcripción)
                          └──▶ Redis (cache)
```

## Servicios

| Puerto | Servicio |
|--------|----------|
| 3000 | Frontend |
| 8000 | API Backend |
| 5433 | PostgreSQL |
| 6379 | Redis |
| 9000 | MinIO (S3) |
| 9001 | MinIO Console |

## Documentación

- [CONTEXTO.md](CONTEXTO.md) - Documentación técnica completa
- http://localhost:8000/docs - Swagger API

## Stack Tecnológico

- **Frontend**: Next.js 14, React, TailwindCSS
- **Backend**: FastAPI, Python 3.13, SQLAlchemy
- **Base de datos**: PostgreSQL 15
- **Almacenamiento**: MinIO (S3 compatible)
- **IA**: Whisper, FHIR Mapper
- **Video**: PeerJS (WebRTC P2P)
