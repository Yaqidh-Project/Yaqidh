import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.inference import model_inference
from app.services.retention import retention_loop
from app.routers import auth, users, zones, cameras, incidents, reports, inference, websocket
from app.routers import manager as manager_router
from app.services.notifications import manager as ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Yaqidh API server...")

    logger.info("Loading ONNX models...")
    model_inference.load_models()

    retention_task = asyncio.create_task(retention_loop())
    logger.info(f"Clip retention task started (retention: {settings.CLIP_RETENTION_DAYS} days)")

    yield

    retention_task.cancel()
    try:
        await retention_task
    except asyncio.CancelledError:
        pass
    logger.info("Yaqidh API server shutdown complete.")


app = FastAPI(
    title="Yaqidh API",
    description="AI-powered child safety monitoring backend — Fall Detection & Violence Detection",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/yaqidh-api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(manager_router.router)
app.include_router(users.router)
app.include_router(zones.router)
app.include_router(cameras.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(inference.router)
app.include_router(websocket.router)


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "service": "yaqidh-api",
        "fall_model_loaded": model_inference.fall_session is not None,
        "violence_model_loaded": model_inference.violence_session is not None,
        "active_ws_connections": ws_manager.active_count,
    }
