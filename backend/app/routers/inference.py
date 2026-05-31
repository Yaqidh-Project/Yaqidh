import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
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

def _resolve_clip_extension(upload: UploadFile) -> str:
    """
    Derive the correct file extension from the upload.
    Priority: content_type → filename suffix → fallback .webm
    Never returns .bin.
    """
    if upload.content_type and upload.content_type in VIDEO_EXTENSIONS:
        return VIDEO_EXTENSIONS[upload.content_type]

    if upload.filename:
        suffix = Path(upload.filename).suffix.lower()
        if suffix and suffix != ".bin":
            return suffix

    return ".webm"


async def _get_zone_users(camera_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    """ Fetches all unique user IDs linked to the camera's specific zone structure """
    result = await db.execute(
        select(User.user_id)
        .join(Zone.users)
        .join(Zone.cameras)
        .where(Camera.camera_id == camera_id)
    )
    return [row[0] for row in result.all()]


async def _assert_camera_access(user: User, camera_id: uuid.UUID, db: AsyncSession) -> None:
    """ Security gate ensuring assigned staff or parents have clearance for this specific hardware node """
    if user.role_name in ["Manager", "Parent"]:
        return

    result = await db.execute(
        select(Camera)
        .join(Camera.zone)
        .join(Zone.users)
        .where(Camera.camera_id == camera_id, User.user_id == user.user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you are not assigned to this camera's zone",
        )


async def _save_incident_clip(
    clip: Optional[UploadFile],
    clip_bytes: Optional[bytes],
    incident_id: uuid.UUID,
) -> Optional[str]:
    """
    Persists the video clip to disk and returns the public URL path.
    """
    if clip is None or not clip_bytes:
        return None

    try:
        clips_dir = settings.CLIPS_DIR
        clips_dir.mkdir(parents=True, exist_ok=True)
        ext = _resolve_clip_extension(clip)
        dest = clips_dir / f"{incident_id}{ext}"
        dest.write_bytes(clip_bytes)
        logger.info(f"Clip saved → {dest} ({len(clip_bytes)} bytes)")
        return f"/incident_clips/{dest.name}"
    except Exception as e:
        logger.warning(f"Could not save clip file: {e}")
        return None


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    model_name: str = Form(..., description="fall_detection or violence_detection"),
    camera_id: uuid.UUID = Form(...),
    frame: Optional[UploadFile] = File(None, description="JPEG or PNG frame for image-based inference"),
    clip: Optional[UploadFile] = File(None, description="Video clip for clip-based inference"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if model_name not in ("fall_detection", "violence_detection"):
        raise HTTPException(status_code=422, detail="model_name must be fall_detection or violence_detection")

    if frame is None and clip is None:
        raise HTTPException(status_code=422, detail="Provide either 'frame' (image) or 'clip' (video) for inference")

    cam_result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, camera_id, db)

    if frame is not None:
        image_bytes = await frame.read()
        is_video = False
    else:
        image_bytes = await clip.read()
        is_video = True

    clip_bytes: Optional[bytes] = None
    if clip is not None and frame is not None:
        clip_bytes = await clip.read()
    elif clip is not None:
        clip_bytes = image_bytes

    prediction = model_inference.predict(model_name, image_bytes, is_video=is_video)

    label = prediction["label"]
    confidence = prediction["confidence"]
    incident_created = False
    incident_id = None
    clip_path_saved = None

    positive_labels = {"fall", "violence"}
    threshold = (
        settings.FALL_CONFIDENCE_THRESHOLD
        if model_name == "fall_detection"
        else settings.VIOLENCE_CONFIDENCE_THRESHOLD
    )

    if str(label).lower() in positive_labels and confidence >= threshold:
        from app.models.incident import Incident

        if model_name == "fall_detection":
            calculated_severity = "Critical" if confidence >= 0.60 else "Warning"
        else:
            calculated_severity = "Critical" if confidence >= 0.70 else "Warning"

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

        clip_path_saved = await _save_incident_clip(clip, clip_bytes, incident_id)
        if clip_path_saved:
            incident.incident_clip = clip_path_saved
            await db.flush()

        user_ids = await _get_zone_users(camera_id, db)
        
        # await to guarantee execution before response context terminates
        await ws_manager.notify_incident(
            user_ids,
            incident_id=incident.incident_id,
            incident_type=str(label).lower(),
            danger_category=calculated_severity,
            camera_id=camera_id,
            confidence=confidence,
            timestamp=incident.timestamp,
            incident_clip=clip_path_saved,
            stub=prediction.get("stub", False),
        )

    await db.commit()
    return PredictionResponse(
        model=model_name,
        label=label,
        confidence=confidence,
        incident_created=incident_created,
        incident_id=incident_id,
    )


@router.post("/detect", response_model=CombinedPredictionResponse)
async def detect_both(
    camera_id: uuid.UUID = Form(...),
    frame: Optional[UploadFile] = File(None, description="JPEG or PNG frame for image-based inference"),
    clip: Optional[UploadFile] = File(None, description="Video clip for clip-based inference"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if frame is None and clip is None:
        raise HTTPException(status_code=422, detail="Provide either 'frame' (image) or 'clip' (video) for inference")

    cam_result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, camera_id, db)

    if frame is not None:
        image_bytes = await frame.read()
        is_video = False
    else:
        image_bytes = await clip.read()
        is_video = True

    clip_bytes: Optional[bytes] = None
    if clip is not None and frame is not None:
        clip_bytes = await clip.read()
    elif clip is not None:
        clip_bytes = image_bytes

    results = model_inference.predict_both(image_bytes, is_video=is_video)
    fall_result = results["fall_detection"]
    violence_result = results["violence_detection"]

    incident_created = False
    incidents: list[dict] = []

    positive_labels = {"fall", "violence"}
    fall_label = fall_result["label"]
    fall_confidence = fall_result["confidence"]
    violence_label = violence_result["label"]
    violence_confidence = violence_result["confidence"]

    is_fall_valid = (
        str(fall_label).lower() in positive_labels
        and fall_confidence >= settings.FALL_CONFIDENCE_THRESHOLD
    )
    is_violence_valid = (
        str(violence_label).lower() in positive_labels
        and violence_confidence >= settings.VIOLENCE_CONFIDENCE_THRESHOLD
    )

    if is_fall_valid and (
        violence_confidence > fall_confidence
        and str(violence_label).lower() in positive_labels
    ):
        logger.info("Fall detection blocked: dynamic action features highly lean toward violence distribution bounds.")
        is_fall_valid = False

    # ── Fall incident ─────────────────────────────────────────────────────────
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

        clip_path_saved = await _save_incident_clip(clip, clip_bytes, incident.incident_id)
        if clip_path_saved:
            incident.incident_clip = clip_path_saved
            await db.flush()

        user_ids = await _get_zone_users(camera_id, db)
        
        # await to prevent request context from closing prematurely
        await ws_manager.notify_incident(
            user_ids,
            incident_id=incident.incident_id,
            incident_type="fall",
            danger_category=fall_severity,
            camera_id=camera_id,
            confidence=fall_confidence,
            timestamp=incident.timestamp,
            incident_clip=clip_path_saved,
            stub=fall_result.get("stub", False),
        )
        incidents.append({
            "incident_id": str(incident.incident_id),
            "danger_category": fall_severity,
            "incident_type": "fall",
            "confidence": fall_confidence,
        })

    # ── Violence incident ─────────────────────────────────────────────────────
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

        clip_path_saved = await _save_incident_clip(clip, clip_bytes, incident.incident_id)
        if clip_path_saved:
            incident.incident_clip = clip_path_saved
            await db.flush()

        user_ids = await _get_zone_users(camera_id, db)
        
        # await to prevent request context from closing prematurely
        await ws_manager.notify_incident(
            user_ids,
            incident_id=incident.incident_id,
            incident_type="violence",
            danger_category=violence_severity,
            camera_id=camera_id,
            confidence=violence_confidence,
            timestamp=incident.timestamp,
            incident_clip=clip_path_saved,
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