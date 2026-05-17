"""
Real-time camera testing script for Yaqidh AI safety system.

Captures frames from webcam, sends to backend /inference/detect endpoint,
visualizes detection results with OpenCV overlays, and logs full detection flow.

IMPORTANT:
- Uses backend detection as single source of truth
- Visualization and temporal counters are for testing/debugging only
- Does NOT duplicate backend detection logic
"""

import cv2
import requests
import numpy as np
import time
import uuid
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000/yaqidh-api"
INFERENCE_ENDPOINT = f"{API_BASE_URL}/inference/detect"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# Frame processing
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
INFERENCE_INTERVAL = 2  # Run inference every N frames
FPS_LIMIT = 30

# Temporal verification thresholds (for visualization only)
FALL_THRESHOLD = 3
VIOLENCE_THRESHOLD = 3

# Confidence thresholds (matching backend)
FALL_CONFIDENCE_THRESHOLD = 0.7
VIOLENCE_CONFIDENCE_THRESHOLD = 0.4

# Auth credentials for testing
# These should match a user in your database
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test-password"
TEST_CAMERA_ID = None  # Will be set from user input or config


class DetectionState:
    """Tracks detection state for visualization."""

    def __init__(self):
        self.fall_counter = 0
        self.violence_counter = 0
        self.last_fall_detection = None
        self.last_violence_detection = None
        self.motion_score = 0.0
        self.prev_frame = None


def calculate_motion_score(frame: np.ndarray, prev_frame: Optional[np.ndarray]) -> float:
    """Calculate motion score using frame differencing."""
    if prev_frame is None:
        return 0.0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(gray, gray_prev)
    motion = np.sum(diff) / (frame.shape[0] * frame.shape[1]) / 255.0
    return min(motion, 1.0)


def draw_detection_boxes(
    frame: np.ndarray,
    fall_detection: Dict[str, Any],
    violence_detection: Dict[str, Any]
) -> np.ndarray:
    """Draw bounding boxes from backend detection response."""

    # Backend detection dicts contain: label, confidence, and optionally boxes
    # Only draw if backend provided box coordinates

    for detection_type, detection in [("fall", fall_detection), ("violence", violence_detection)]:
        if not detection or detection.get("label") == "no_detection":
            continue

        # Check if backend provided bounding box data
        if "boxes" in detection and detection["boxes"]:
            boxes = detection["boxes"]
            if isinstance(boxes, list) and len(boxes) > 0:
                for box in boxes:
                    if isinstance(box, (list, tuple)) and len(box) >= 4:
                        x1, y1, x2, y2 = box[:4]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                        # Draw rectangle
                        color = (0, 0, 255) if detection_type == "fall" else (255, 0, 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                        # Draw label with confidence
                        label = f"{detection_type.upper()}: {detection['confidence']:.2f}"
                        cv2.putText(
                            frame, label,
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                        )

    return frame


def draw_overlay_text(
    frame: np.ndarray,
    state: DetectionState,
    fps_actual: float,
    fall_confidence: float = 0.0,
    violence_confidence: float = 0.0
) -> np.ndarray:
    """Draw real-time visualization overlays on frame.

    Uses actual confidence thresholds:
    - Fall: 0.7
    - Violence: 0.4
    """

    # FPS
    cv2.putText(
        frame, f"FPS: {fps_actual:.1f}",
        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2
    )

    # Motion Score
    cv2.putText(
        frame, f"Motion Score: {state.motion_score:.2f}",
        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2
    )

    # Temporal Verification - Fall Counter (only if confidence >= 0.7)
    if fall_confidence >= FALL_CONFIDENCE_THRESHOLD:
        cv2.putText(
            frame, f"Fall Counter: {state.fall_counter}/{FALL_THRESHOLD}",
            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )
    else:
        cv2.putText(
            frame, f"Fall Counter: 0/{FALL_THRESHOLD}",
            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2
        )

    # Temporal Verification - Violence Counter (only if confidence >= 0.4)
    if violence_confidence >= VIOLENCE_CONFIDENCE_THRESHOLD:
        cv2.putText(
            frame, f"Violence Counter: {state.violence_counter}/{VIOLENCE_THRESHOLD}",
            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )
    else:
        cv2.putText(
            frame, f"Violence Counter: 0/{VIOLENCE_THRESHOLD}",
            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2
        )

    # Fall Detection Confidence (only if >= 0.7)
    if fall_confidence >= FALL_CONFIDENCE_THRESHOLD:
        cv2.putText(
            frame, f"Fall: {fall_confidence:.2f} ✓",
            (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )
    else:
        cv2.putText(
            frame, f"Fall: {fall_confidence:.2f}",
            (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2
        )

    # Violence Detection Confidence (only if >= 0.4)
    if violence_confidence >= VIOLENCE_CONFIDENCE_THRESHOLD:
        cv2.putText(
            frame, f"Violence: {violence_confidence:.2f} ✓",
            (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )
    else:
        cv2.putText(
            frame, f"Violence: {violence_confidence:.2f}",
            (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2
        )

    return frame


def get_auth_token(email: str, password: str) -> Optional[str]:
    """Authenticate with backend and get JWT token."""
    try:
        login_url = f"{API_BASE_URL}/auth/login"
        response = requests.post(
            login_url,
            json={"email": email, "password": password},
            timeout=5
        )

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            if token:
                logger.info(f"✓ Authenticated as {email}")
                return token
            else:
                logger.error("No token in response")
                return None
        elif response.status_code == 401:
            logger.error(f"Authentication failed - invalid credentials for {email}")
            return None
        else:
            logger.error(f"Login failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


def verify_backend_connectivity() -> bool:
    """Verify that backend API is accessible."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"Backend health: {health_data}")

            if not health_data.get("fall_model_loaded") or not health_data.get("violence_model_loaded"):
                logger.warning("Models not fully loaded on backend")
                return True  # Continue anyway, models may load later

            return True
    except Exception as e:
        logger.error(f"Backend connectivity check failed: {e}")
        return False


def send_frame_for_inference(
    frame: np.ndarray,
    camera_id: str,
    token: str
) -> Optional[Dict[str, Any]]:
    """Send frame to backend /inference/detect endpoint."""

    try:
        # Encode frame as JPEG
        _, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # Prepare multipart form data
        files = {
            'frame': ('frame.jpg', jpeg_data.tobytes(), 'image/jpeg')
        }
        data = {
            'camera_id': camera_id
        }
        headers = {
            'Authorization': f'Bearer {token}'
        }

        response = requests.post(
            INFERENCE_ENDPOINT,
            files=files,
            data=data,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logger.error("Authentication failed - check your token")
            return None
        else:
            logger.warning(f"Inference request failed: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send frame for inference: {e}")
        return None


def log_detection_results(
    response: Dict[str, Any],
    frame_num: int
) -> None:
    """Log detection results in structured format."""

    fall = response.get("fall_detection", {})
    violence = response.get("violence_detection", {})
    incident_created = response.get("incident_created", False)
    incidents = response.get("incidents", [])

    logger.info(f"\n{'='*60}")
    logger.info(f"Frame #{frame_num} - Detection Results")
    logger.info(f"{'='*60}")

    # Fall Detection
    logger.info(f"Fall Detection: label={fall.get('label')}, "
                f"confidence={fall.get('confidence', 0):.2f}")

    # Violence Detection
    logger.info(f"Violence Detection: label={violence.get('label')}, "
                f"confidence={violence.get('confidence', 0):.2f}")

    # Incident Status
    logger.info(f"Incident Created: {incident_created}")

    # Incidents List
    if incidents:
        logger.info(f"Created Incidents ({len(incidents)}):")
        for inc in incidents:
            logger.info(f"  - ID: {inc.get('incident_id')}, "
                       f"Category: {inc.get('danger_category')}, "
                       f"Type: {inc.get('incident_type')}, "
                       f"Confidence: {inc.get('confidence', 0):.2f}")

    logger.info(f"{'='*60}\n")


def update_temporal_counters(
    state: DetectionState,
    fall_label: str,
    fall_confidence: float,
    violence_label: str,
    violence_confidence: float
) -> None:
    """Update temporal verification counters based on detection results and thresholds.

    Fall threshold: 0.7
    Violence threshold: 0.4
    """

    # Fall detection - update counter only if confidence >= 0.7
    if fall_label == "fall" and fall_confidence >= 0.7:
        state.fall_counter = min(state.fall_counter + 1, FALL_THRESHOLD)
    else:
        state.fall_counter = 0

    # Violence detection - update counter only if confidence >= 0.4
    if violence_label == "violence" and violence_confidence >= 0.4:
        state.violence_counter = min(state.violence_counter + 1, VIOLENCE_THRESHOLD)
    else:
        state.violence_counter = 0


def run_realtime_detection(camera_id: str, token: str) -> None:
    """Main real-time detection loop."""

    # Verify backend connectivity first
    if not verify_backend_connectivity():
        logger.error("Cannot connect to backend. Ensure it's running on http://localhost:8000")
        logger.error(f"Trying to reach: {HEALTH_ENDPOINT}")
        sys.exit(1)

    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Failed to open webcam")
        sys.exit(1)

    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    state = DetectionState()
    frame_count = 0
    fps_clock = time.time()
    fps_frames = 0
    fps_actual = 0

    logger.info(f"Starting real-time detection loop for camera {camera_id}")
    logger.info(f"Press 'q' to exit, 'p' to pause/resume, 's' to save frame")
    logger.info(f"Backend: {API_BASE_URL}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to read frame from webcam")
                break

            frame_count += 1
            fps_frames += 1

            # Resize frame
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # Calculate motion score
            state.motion_score = calculate_motion_score(frame, state.prev_frame)
            state.prev_frame = frame.copy()

            # Run inference every N frames
            fall_confidence = 0.0
            violence_confidence = 0.0

            if frame_count % INFERENCE_INTERVAL == 0:
                logger.info(f"Sending frame {frame_count} for inference...")
                response = send_frame_for_inference(frame, camera_id, token)

                if response:
                    fall = response.get("fall_detection", {})
                    violence = response.get("violence_detection", {})

                    fall_label = fall.get("label", "no_detection")
                    violence_label = violence.get("label", "no_detection")
                    fall_confidence = fall.get("confidence", 0.0)
                    violence_confidence = violence.get("confidence", 0.0)

                    # Log full detection flow
                    log_detection_results(response, frame_count)

                    # Update temporal counters (pass confidence values to respect thresholds)
                    update_temporal_counters(state, fall_label, fall_confidence, violence_label, violence_confidence)

                    # Draw detection boxes from backend response
                    frame = draw_detection_boxes(frame, fall, violence)

                    # Log notification recipients and broadcast status
                    if response.get("incident_created"):
                        logger.info("✓ Incident created - WebSocket broadcast triggered")
                        logger.info("✓ Notifications sent to zone users")
                        if response.get("incidents"):
                            for inc in response.get("incidents"):
                                logger.info(f"  Incident {inc.get('incident_id')} "
                                           f"({inc.get('danger_category')})")

            # Draw overlay text
            frame = draw_overlay_text(frame, state, fps_actual, fall_confidence, violence_confidence)

            # Display frame
            cv2.imshow("Yaqidh Real-time Detection", frame)

            # FPS calculation
            current_time = time.time()
            if current_time - fps_clock >= 1.0:
                fps_actual = fps_frames / (current_time - fps_clock)
                fps_frames = 0
                fps_clock = current_time

            # FPS limiting
            key = cv2.waitKey(max(1, int(1000 / FPS_LIMIT))) & 0xFF

            if key == ord('q'):
                logger.info("Exiting...")
                break
            elif key == ord('p'):
                logger.info("Paused - press 'p' again to resume")
                while True:
                    if cv2.waitKey(0) & 0xFF == ord('p'):
                        break
            elif key == ord('s'):
                filename = f"detection_frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                logger.info(f"Frame saved: {filename}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Cleanup complete")


def main():
    """Entry point."""

    logger.info("="*70)
    logger.info("Yaqidh Real-time Camera Testing Script")
    logger.info("="*70)
    logger.info(f"API Base: {API_BASE_URL}\n")

    # Get camera ID from user or config
    camera_id = TEST_CAMERA_ID
    if not camera_id:
        camera_id_input = input("Enter camera ID (or press Enter for random UUID): ").strip()
        camera_id = camera_id_input if camera_id_input else str(uuid.uuid4())

    logger.info(f"Camera ID: {camera_id}\n")

    # Authenticate
    logger.info("Authenticating...")
    email = input(f"Email (default: {TEST_EMAIL}): ").strip() or TEST_EMAIL
    password = input(f"Password (default: {TEST_PASSWORD}): ").strip() or TEST_PASSWORD

    token = get_auth_token(email, password)
    if not token:
        logger.error("Failed to authenticate. Ensure test user exists in database:")
        logger.error(f"  Email: {email}")
        logger.error(f"  Password: {password}")
        logger.error("\nYou can create a test user via the /auth/register endpoint")
        sys.exit(1)

    logger.info("")
    run_realtime_detection(camera_id, token)


if __name__ == "__main__":
    main()
