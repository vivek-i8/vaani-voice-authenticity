from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.ml.model_loader import initialize_models, cleanup_models
from app.api.analyze import analyze_router
from app.api.model_card import router as model_card_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_models()
    yield
    # Shutdown
    await cleanup_models()


app = FastAPI(
    title="VAANI - Voice Authenticity Analysis",
    description="Multi-signal voice authenticity analysis system",
    version="2.0.0-alpha",
    lifespan=lifespan,
)

# Add CORS middleware for frontend integration
# V2: Cloudflare Pages frontend; allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# V2: single active API path only
app.include_router(analyze_router, prefix="/api", tags=["analysis"])
app.include_router(model_card_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint that reports actual model status."""
    from app.ml.model_loader import get_model_status

    return get_model_status()
