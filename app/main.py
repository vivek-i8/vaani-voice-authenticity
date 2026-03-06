from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.ml.model_loader import initialize_model, cleanup_model
from app.api.routes import router
from app.api.analyze import analyze_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_model()
    yield
    # Shutdown
    await cleanup_model()


app = FastAPI(
    title="Vaani - Voice Authenticity Detection",
    description="AI-powered voice authenticity detection system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["analysis"])
app.include_router(analyze_router, prefix="/api", tags=["analysis"])