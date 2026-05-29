import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.camera import Camera
from app.models.zone import Zone
from app.models.user import User
from app.schemas.inference import PredictionResponse, CombinedPredictionResponse
from app.auth.dependencies import get_current_user
from app.services.inference import model_inference
from app.services.notifications import manager as ws_manager
from app.config import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inference", tags=["inference"])
settings = get_settings()

# ─── Supported video MIME types ──────────────────────────────────────────────
VIDEO_EXTENSIONS = {
    "video/webm": ".webm",
    "video/mp4": ".mp4",
    "video/ogg": ".ogv",
    "video/x-matroska": ".mkv",
}

def _resolve_clip_extension(content_type: Optional[str], filename: Optional[str]) -> str:
    if content_type and content_type in VIDEO_EXTENSIONS:
        return VIDEO_EXTENSIONS[content_type]
    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix and suffix != ".bin":
            return suffix
    return ".webm"


def _save_clip_background(clip_bytes: bytes, incident_id: uuid.UUID, content_type: Optional[str], filename: Optional[str]):
    """
    ✅ PRODUCTION FIX: Saved asynchronously in the background.
    Prevents CPU choking and blocks during core AI inference loops.
    """
    try:
        clips_dir = settings.CLIPS_DIR
        clips_dir.mkdir(parents=True, exist_ok=True)
        ext = _resolve_clip_extension(content_type, filename)
        dest = clips_dir / f"{incident_id}{ext}"
        dest.write_bytes(clip_bytes)
        logger.info(f"✅ [Background Task] Clip saved successfully -> {dest} ({len(clip_bytes)} bytes)")
    except Exception as e:
        logger.warning(f"❌ Background task failed to save clip file: {e}")


async def _get_zone_users(camera_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    zone_result = await db.execute(select(Zone).join(Camera).where(Camera.camera_id == camera_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        return []
    
    result = await db.execute(select(User.user_id).join(Zone.users).where(Zone.zone_id == zone.zone_id))
    zone_users = [row[0] for row in result.all()]
    
    manager_result = await db.execute(select(User.user_id).where(User.role_name == "Manager"))
    managers = [row[0] for row in manager_result.all()]
    
    return list(set(zone_users + managers))


async def _assert_camera_access(user: User, camera_id: uuid.UUID, db: AsyncSession) -> None:
    if user.role_name in ["Manager", "Parent"]:
        return
    result = await db.execute(
        select(Camera).join(Camera.zone).join(Zone.users).where(Camera.camera_id == camera_id, User.user_id == user.user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this camera's zone")


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    background_tasks: BackgroundTasks,
    model_name: str = Form(..., description="fall_detection or violence_detection"),
    camera_id: uuid.UUID = Form(...),
    frame: Optional[UploadFile] = File(None),
    clip: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if model_name not in ("fall_detection", "violence_detection"):
        raise HTTPException(status_code=422, detail="Invalid model_name")

    if frame is None and clip is None:
        raise HTTPException(status_code=422, detail="Provide either 'frame' or 'clip'")

    cam_result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, camera_id, db)

    # Core raw data reading sequence
    image_bytes = await frame.read() if frame is not None else await clip.read()
    is_video = frame is None

    clip_bytes = None
    if clip is not None:
        clip_bytes = await clip.read() if frame is not None else image_bytes

    # Clean non-blocking image inference operation
    prediction = model_inference.predict(model_name, image_bytes, is_video=is_video)
    label = prediction["label"]
    confidence = prediction["confidence"]
    incident_created = False
    incident_id = None

    positive_labels = {"fall", "violence"}
    threshold = settings.FALL_CONFIDENCE_THRESHOLD if model_name == "fall_detection" else settings.VIOLENCE_CONFIDENCE_THRESHOLD

    if str(label).lower() in positive_labels and confidence >= threshold:
        from app.models.incident import Incident
        calculated_severity = "Critical" if (model_name == "fall_detection" and confidence >= 0.60) or (model_name == "violence_detection" and confidence >= 0.70) else "Warning"

        incident = Incident(
            danger_category=calculated_severity,
            incident_type=str(label).lower(),
            camera_id=camera_id,
            confidence=confidence,
            status="open",
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        incident_created = True
        incident_id = incident.incident_id

        if clip_bytes:
            ext = _resolve_clip_extension(clip.content_type, clip.filename)
            clip_url = f"https://yaqidh-backend.onrender.com/clips/{incident_id}{ext}"
            incident.incident_clip = clip_url
            await db.flush()
            # Offload heavy IO storage tasks seamlessly to the background thread pool
            background_tasks.add_task(_save_clip_background, clip_bytes, incident_id, clip.content_type, clip.filename)

        user_ids = await _get_zone_users(camera_id, db)
        await ws_manager.notify_incident(
            user_ids,
            incident_id=incident.incident_id,
            incident_type=str(label).lower(),
            danger_category=calculated_severity,
            camera_id=camera_id,
            confidence=confidence,
            timestamp=incident.timestamp,
            incident_clip=incident.incident_clip,
            stub=prediction.get("stub", False),
        )

    await db.commit()
    return PredictionResponse(
        model=model_name, label=label, confidence=confidence, incident_created=incident_created, incident_id=incident_id
    )


@router.post("/detect", response_model=CombinedPredictionResponse)
async def detect_both(
    background_tasks: BackgroundTasks,
    camera_id: uuid.UUID = Form(...),
    frame: Optional[UploadFile] = File(None),
    clip: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if frame is None and clip is None:
        raise HTTPException(status_code=422, detail="Provide either 'frame' or 'clip'")

    cam_result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, camera_id, db)

    image_bytes = await frame.read() if frame is not None else await clip.read()
    is_video = frame is None

    clip_bytes = None
    if clip is not None:
        clip_bytes = await clip.read() if frame is not None else image_bytes

    # ✅ STEP INTEGRATION: Instant Frame-Only AI Evaluation Sequence
    results = model_inference.predict_both(image_bytes, is_video=is_video)
    fall_result = results["fall_detection"]
    violence_result = results["violence_detection"]

    incident_created = False
    incidents = []

    positive_labels = {"fall", "violence"}
    fall_confidence = fall_result["confidence"]
    violence_confidence = violence_result["confidence"]

    is_fall_valid = str(fall_result["label"]).lower() in positive_labels and fall_confidence >= settings.FALL_CONFIDENCE_THRESHOLD
    is_violence_valid = str(violence_result["label"]).lower() in positive_labels and violence_confidence >= settings.VIOLENCE_CONFIDENCE_THRESHOLD

    if is_fall_valid and violence_confidence > fall_confidence and str(violence_result["label"]).lower() in positive_labels:
        is_fall_valid = False

    # ── Fall incident execution bounds ────────────────────────────────────────
    if is_fall_valid:
        from app.models.incident import Incident
        fall_severity = "Critical" if fall_confidence >= 0.70 else "Warning"
        incident = Incident(
            danger_category=fall_severity,
            incident_type="fall",
            camera_id=camera_id,
            confidence=fall_confidence,
            status="open",
            detections={"fall_detection": fall_result, "violence_detection": violence_result},
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        incident_created = True

        if clip_bytes:
            ext = _resolve_clip_extension(clip.content_type, clip.filename)
            clip_url = f"https://yaqidh-backend.onrender.com/clips/{incident.incident_id}{ext}"
            incident.incident_clip = clip_url
            await db.flush()
            background_tasks.add_task(_save_clip_background, clip_bytes, incident.incident_id, clip.content_type, clip.filename)

        user_ids = await _get_zone_users(camera_id, db)
        await ws_manager.notify_incident(
            user_ids,
            incident_id=incident.incident_id,
            incident_type="fall",
            danger_category=fall_severity,
            camera_id=camera_id,
            confidence=fall_confidence,
            timestamp=incident.timestamp,
            incident_clip=incident.incident_clip,
            stub=fall_result.get("stub", False),
        )
        incidents.append({
            "incident_id": str(incident.incident_id),
            "danger_category": fall_severity,
            "incident_type": "fall",
            "confidence": fall_confidence,
        })

    # ── Violence incident execution bounds ────────────────────────────────────
    if is_violence_valid and not incident_created:
        from app.models.incident import Incident
        violence_severity = "Critical" if violence_confidence >= 0.85 else "Warning"
        incident = Incident(
            danger_category=violence_severity,
            incident_type="violence",
            camera_id=camera_id,
            confidence=violence_confidence,
            status="open",
            detections={"fall_detection": fall_result, "violence_detection": violence_result},
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        incident_created = True

        if clip_bytes:
            ext = _resolve_clip_extension(clip.content_type, clip.filename)
            clip_url = f"https://yaqidh-backend.onrender.com/clips/{incident.incident_id}{ext}"
            incident.incident_clip = clip_url
            await db.flush()
            background_tasks.add_task(_save_clip_background, clip_bytes, incident.incident_id, clip.content_type, clip.filename)

        user_ids = await _get_zone_users(camera_id, db)
        await ws_manager.notify_incident(
            user_ids,
            incident_id=incident.incident_id,
            incident_type="violence",
            danger_category=violence_severity,
            camera_id=camera_id,
            confidence=violence_confidence,
            timestamp=incident.timestamp,
            incident_clip=incident.incident_clip,
            stub=violence_result.get("stub", False),
        )
        incidents.append({
            "incident_id": str(incident.incident_id),
            "danger_category": violence_severity,
            "incident_type": "violence",
            "confidence": violence_confidence,
        })

    await db.commit()
    return CombinedPredictionResponse(
        fall_detection=fall_result,
        violence_detection=violence_result,
        incident_created=incident_created,
        incidents=incidents if incidents else None,
    )


@router.get("/status")
async def inference_status(current_user: User = Depends(get_current_user)):
    from app.services.inference import ONNX_AVAILABLE
    return {
        "fall_detection": model_inference.fall_session is not None,
        "violence_detection": model_inference.violence_session is not None,
        "onnx_available": ONNX_AVAILABLE,
    }