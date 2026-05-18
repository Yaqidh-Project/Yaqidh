import uuid
from pathlib import Path
from datetime import datetime
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


async def _get_zone_users(camera_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(User.user_id)
        .join(Zone.users)
        .join(Zone.cameras)
        .where(Camera.camera_id == camera_id)
    )
    return [row[0] for row in result.all()]


async def _assert_camera_access(user: User, camera_id: uuid.UUID, db: AsyncSession) -> None:
    if user.role_name == "Manager":
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
        clip_filename = None
        is_video = False
    else:
        image_bytes = await clip.read()
        clip_filename = clip.filename
        is_video = True

    prediction = model_inference.predict(model_name, image_bytes, is_video=is_video)

    label = prediction["label"]
    confidence = prediction["confidence"]
    incident_created = False
    incident_id = None
    clip_path_saved = None

    positive_labels = {"fall", "violence"}
    # Use model-specific threshold
    threshold = settings.CONFIDENCE_THRESHOLD if model_name == "fall_detection" else settings.VIOLENCE_CONFIDENCE_THRESHOLD
    if label in positive_labels and confidence >= threshold:
        from app.models.incident import Incident

        danger_category = "fall" if model_name == "fall_detection" else "violence"
        incident = Incident(
            danger_category=danger_category,
            incident_type=label,
            camera_id=camera_id,
            confidence=confidence,
            status="open",
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        incident_created = True
        incident_id = incident.incident_id

        if clip is not None and image_bytes:
            try:
                clips_dir = Path(settings.CLIPS_DIR)
                clips_dir.mkdir(parents=True, exist_ok=True)
                ext = Path(clip_filename or "clip.bin").suffix or ".bin"
                dest = clips_dir / f"{incident_id}{ext}"
                dest.write_bytes(image_bytes)
                clip_path_saved = f"/incident_clips/{dest.name}"
                incident.incident_clip = clip_path_saved
                await db.flush()
            except Exception as e:
                logger.warning(f"Could not save clip file: {e}")

        user_ids = await _get_zone_users(camera_id, db)
        await ws_manager.broadcast_to_users(
            user_ids,
            {
                "event": "incident_detected",
                "incident_id": str(incident.incident_id),
                "danger_category": danger_category,
                "incident_type": label,
                "camera_id": str(camera_id),
                "confidence": confidence,
                "timestamp": incident.timestamp.isoformat(),
                "incident_clip": clip_path_saved,
                "stub": prediction.get("stub", False),
            },
        )

    return PredictionResponse(
        model=model_name,
        label=label,
        confidence=confidence,
        incident_created=incident_created,
        incident_id=incident_id,
    )


# Cooldown tracking to prevent repeated notifications (in-memory cache)
_detection_cooldowns: dict[tuple[str, str], float] = {}
COOLDOWN_SECONDS = 60  # Prevent same detection type on same camera for 60 seconds


@router.post("/detect", response_model=CombinedPredictionResponse)
async def detect_both(
    camera_id: uuid.UUID = Form(...),
    frame: Optional[UploadFile] = File(None, description="JPEG or PNG frame for image-based inference"),
    clip: Optional[UploadFile] = File(None, description="Video clip for clip-based inference"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run both fall and violence detection models in parallel on the same frame.
    
    If either model detects danger above the confidence threshold, creates an incident
    and sends a notification. Includes cooldown to prevent repeated notifications.
    """
    if frame is None and clip is None:
        raise HTTPException(status_code=422, detail="Provide either 'frame' (image) or 'clip' (video) for inference")

    cam_result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, camera_id, db)

    if frame is not None:
        image_bytes = await frame.read()
        clip_filename = None
        is_video = False
    else:
        image_bytes = await clip.read()
        clip_filename = clip.filename
        is_video = True

    # Run both models in parallel
    results = model_inference.predict_both(image_bytes, is_video=is_video)

    fall_result = results["fall_detection"]
    violence_result = results["violence_detection"]

    incident_created = False
    incidents: list[dict] = []

    # Check cooldown for fall detection
    fall_label = fall_result["label"]
    fall_confidence = fall_result["confidence"]
    fall_incident_created = False

    positive_labels = {"fall", "violence"}
    if fall_label in positive_labels and fall_confidence >= settings.CONFIDENCE_THRESHOLD:
        cooldown_key = (str(camera_id), "fall")
        now = datetime.now().timestamp()
        last_incident_time = _detection_cooldowns.get(cooldown_key, 0)
        
        if now - last_incident_time >= COOLDOWN_SECONDS:
            from app.models.incident import Incident

            incident = Incident(
                danger_category="fall",
                incident_type=fall_label,
                camera_id=camera_id,
                confidence=fall_confidence,
                status="open",
                detections={"fall_detection": fall_result, "violence_detection": violence_result},
            )
            db.add(incident)
            await db.flush()
            await db.refresh(incident)
            fall_incident_created = True
            incident_created = True
            _detection_cooldowns[cooldown_key] = now

            # Save clip if provided
            clip_path_saved = None
            if clip is not None and image_bytes:
                try:
                    clips_dir = Path(settings.CLIPS_DIR)
                    clips_dir.mkdir(parents=True, exist_ok=True)
                    ext = Path(clip_filename or "clip.bin").suffix or ".bin"
                    dest = clips_dir / f"{incident.incident_id}{ext}"
                    dest.write_bytes(image_bytes)
                    clip_path_saved = f"/incident_clips/{dest.name}"
                    incident.incident_clip = clip_path_saved
                    await db.flush()
                except Exception as e:
                    logger.warning(f"Could not save clip file: {e}")

            # Broadcast notification
            user_ids = await _get_zone_users(camera_id, db)
            await ws_manager.broadcast_to_users(
                user_ids,
                {
                    "event": "incident_detected",
                    "incident_id": str(incident.incident_id),
                    "danger_category": "fall",
                    "incident_type": fall_label,
                    "camera_id": str(camera_id),
                    "confidence": fall_confidence,
                    "timestamp": incident.timestamp.isoformat(),
                    "incident_clip": clip_path_saved,
                    "stub": fall_result.get("stub", False),
                },
            )

            incidents.append({
                "incident_id": str(incident.incident_id),
                "danger_category": "fall",
                "incident_type": fall_label,
                "confidence": fall_confidence,
            })

    # Check cooldown for violence detection
    violence_label = violence_result["label"]
    violence_confidence = violence_result["confidence"]
    violence_incident_created = False

    if violence_label in positive_labels and violence_confidence >= settings.VIOLENCE_CONFIDENCE_THRESHOLD:
        cooldown_key = (str(camera_id), "violence")
        now = datetime.now().timestamp()
        last_incident_time = _detection_cooldowns.get(cooldown_key, 0)
        
        if now - last_incident_time >= COOLDOWN_SECONDS:
            from app.models.incident import Incident

            incident = Incident(
                danger_category="violence",
                incident_type=violence_label,
                camera_id=camera_id,
                confidence=violence_confidence,
                status="open",
                detections={"fall_detection": fall_result, "violence_detection": violence_result},
            )
            db.add(incident)
            await db.flush()
            await db.refresh(incident)
            violence_incident_created = True
            incident_created = True
            _detection_cooldowns[cooldown_key] = now

            # Save clip if provided
            clip_path_saved = None
            if clip is not None and image_bytes:
                try:
                    clips_dir = Path(settings.CLIPS_DIR)
                    clips_dir.mkdir(parents=True, exist_ok=True)
                    ext = Path(clip_filename or "clip.bin").suffix or ".bin"
                    dest = clips_dir / f"{incident.incident_id}{ext}"
                    dest.write_bytes(image_bytes)
                    clip_path_saved = f"/incident_clips/{dest.name}"
                    incident.incident_clip = clip_path_saved
                    await db.flush()
                except Exception as e:
                    logger.warning(f"Could not save clip file: {e}")

            # Broadcast notification
            user_ids = await _get_zone_users(camera_id, db)
            await ws_manager.broadcast_to_users(
                user_ids,
                {
                    "event": "incident_detected",
                    "incident_id": str(incident.incident_id),
                    "danger_category": "violence",
                    "incident_type": violence_label,
                    "camera_id": str(camera_id),
                    "confidence": violence_confidence,
                    "timestamp": incident.timestamp.isoformat(),
                    "incident_clip": clip_path_saved,
                    "stub": violence_result.get("stub", False),
                },
            )

            incidents.append({
                "incident_id": str(incident.incident_id),
                "danger_category": "violence",
                "incident_type": violence_label,
                "confidence": violence_confidence,
            })

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
