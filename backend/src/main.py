from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.core.config import settings
from src.routers import auth, users, consultations, fhir, webhooks, ia, livekit, recordings
from src.models.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Telemedicina API",
    description="Backend API para plataforma de telemedicina con videoconsultas P2P, transcripción y FHIR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(consultations.router, prefix="/api/v1/consultations", tags=["consultations"])
app.include_router(fhir.router, prefix="/fhir", tags=["fhir"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(ia.router, prefix="/api/v1/ia", tags=["ia"])
app.include_router(livekit.router, prefix="/api/livekit", tags=["livekit"])
app.include_router(recordings.router, prefix="/api/v1/recordings", tags=["recordings"])


@app.get("/")
async def root():
    return {"message": "Telemedicina API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
