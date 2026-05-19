from ultralytics import YOLO
import cv2
import requests
import numpy as np
import time
import logging
import getpass
from collections import deque
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================

API_BASE_URL = "http://127.0.0.1:8000/yaqidh-api"
REPORT_ENDPOINT = f"{API_BASE_URL}/inference/detect"

BASE_DIR = Path(__file__).resolve().parent.parent / "Backend" / "models"
FALL_MODEL_PATH     = str(BASE_DIR / "fall_detection.onnx")
VIOLENCE_MODEL_PATH = str(BASE_DIR / "violence_detection.onnx")

# Clips saved here (must match backend CLIPS_DIR setting)
CLIPS_DIR = Path(__file__).resolve().parent.parent / "Backend" / "incident_clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# VIDEO SETTINGS
# =========================

FRAME_WIDTH  = 480
FRAME_HEIGHT = 360
INFERENCE_INTERVAL = 4
FPS_LIMIT = 30

CLIP_BUFFER_SECONDS = 5
CLIP_BUFFER_MAXLEN  = CLIP_BUFFER_SECONDS * FPS_LIMIT

# =========================
# THRESHOLDS
# =========================

FALL_CONFIDENCE_THRESHOLD     = 0.7
VIOLENCE_CONFIDENCE_THRESHOLD = 0.4
FALL_THRESHOLD     = 3
VIOLENCE_THRESHOLD = 3


# =========================
# AUTH — LOGIN
# =========================

def login() -> tuple:
    print("\n" + "="*50)
    print("  Yaqidh Real-time Detection")
    print("="*50)

    while True:
        email    = input("\nEnter email: ").strip()
        password = getpass.getpass("Enter password: ")

        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )

            if response.status_code == 200:
                data  = response.json()
                token = data.get("access_token")
                role  = data.get("role", "Unknown")
                logger.info(f"✓ Authenticated as {email} (role: {role})")
                return token, role

            elif response.status_code == 401:
                print("✗ Invalid email or password. Try again.\n")

            else:
                print(f"✗ Login failed: {response.status_code} — {response.text}")
                print("  Try again.\n")

        except Exception as e:
            print(f"✗ Cannot reach backend: {e}")
            print("  Make sure the backend is running on http://127.0.0.1:8000\n")


# =========================
# CAMERA SELECTION
# =========================

def select_camera(token: str, role: str) -> tuple:
    try:
        response = requests.get(
            f"{API_BASE_URL}/cameras",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )

        if response.status_code != 200:
            logger.warning(f"Could not fetch cameras: {response.status_code}")
            camera_id = input("\nEnter camera ID manually: ").strip()
            return camera_id, "Manual"

        cameras = response.json()

        if not cameras:
            logger.warning("No cameras found in database.")
            camera_id = input("\nEnter camera ID manually: ").strip()
            return camera_id, "Manual"

        print("\nAvailable cameras:")
        for i, cam in enumerate(cameras, 1):
            cam_id   = cam.get("camera_id", "?")
            cam_name = cam.get("camera_name", "Unknown")
            zone_id  = cam.get("zone_id", "?")
            status   = cam.get("status", "?")
            print(f"  [{i}] {cam_name}  (zone: {zone_id})  status: {status}")
            print(f"       ID: {cam_id}")

        while True:
            try:
                choice = input(f"\nSelect camera number [1-{len(cameras)}]: ").strip()
                idx    = int(choice) - 1
                if 0 <= idx < len(cameras):
                    selected = cameras[idx]
                    cam_id   = selected.get("camera_id")
                    cam_name = selected.get("camera_name", "Unknown")
                    logger.info(f"✓ Using camera: {cam_name} (ID: {cam_id})")
                    return cam_id, cam_name
                else:
                    print(f"  Please enter a number between 1 and {len(cameras)}")
            except ValueError:
                print("  Please enter a valid number")

    except Exception as e:
        logger.error(f"Error fetching cameras: {e}")
        camera_id = input("\nEnter camera ID manually: ").strip()
        return camera_id, "Manual"


# =========================
# LOAD MODELS
# =========================

def load_models():
    logger.info("Loading models...")
    fall_model     = YOLO(FALL_MODEL_PATH,     task="detect")
    violence_model = YOLO(VIOLENCE_MODEL_PATH, task="detect")
    logger.info("✓ Models loaded successfully")
    return fall_model, violence_model


# =========================
# SAVE CLIP FROM BUFFER
# =========================

def save_clip(frame_buffer: deque, event_type: str) -> tuple:
    """
    Save rolling buffer as .mp4 file.
    Returns (local_path, relative_url).
    relative_url format: /incident_clips/filename.mp4
    """
    timestamp  = time.strftime("%Y%m%d_%H%M%S")
    clip_name  = f"{event_type}_{timestamp}.mp4"
    clip_path  = CLIPS_DIR / clip_name
    clip_url   = f"/incident_clips/{clip_name}"   # relative URL stored in DB

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(clip_path), fourcc, FPS_LIMIT, (FRAME_WIDTH, FRAME_HEIGHT))

    for f in frame_buffer:
        writer.write(f)

    writer.release()
    logger.info(f"✓ Clip saved: {clip_path}")
    logger.info(f"  DB URL: {clip_url}")
    return str(clip_path), clip_url


# =========================
# UPDATE INCIDENT CLIP IN DB
# =========================

def update_incident_clip(incident_id: str, clip_url: str, token: str):
    """
    PATCH the incident with the relative clip URL.
    Stores /incident_clips/filename.mp4 — not a full OS path.
    """
    try:
        response = requests.patch(
            f"{API_BASE_URL}/incidents/{incident_id}",
            json={"incident_clip": clip_url},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if response.status_code == 200:
            logger.info(f"✓ Clip URL saved to DB: {clip_url}")
        else:
            logger.warning(
                f"Could not update incident clip: "
                f"{response.status_code} {response.text}"
            )
    except Exception as e:
        logger.error(f"Clip update error: {e}")


# =========================
# SEND ALERT TO BACKEND
# =========================

def send_alert(frame, frame_buffer: deque, camera_id: str, token: str, event_type: str):
    try:
        # Step 1: Send frame → backend creates incident → returns incident_id
        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        response = requests.post(
            REPORT_ENDPOINT,
            files={"frame": ("frame.jpg", buf.tobytes(), "image/jpeg")},
            data={"camera_id": camera_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if response.status_code != 200:
            logger.warning(f"Alert failed {response.status_code}: {response.text}")
            return

        result = response.json()
        logger.info(f"✓ Alert sent successfully")
        logger.info(f"  Incident created: {result.get('incident_created', False)}")

        incidents = result.get("incidents") or []
        for inc in incidents:
            inc_id = inc.get("incident_id")
            logger.info(
                f"  ⚠️  {str(inc.get('danger_category', '')).upper()} "
                f"ID={inc_id} "
                f"conf={inc.get('confidence', 0):.2f}"
            )

            # Step 2: Save clip locally → update DB with relative URL
            if inc_id:
                _, clip_url = save_clip(frame_buffer, event_type)
                update_incident_clip(inc_id, clip_url, token)

    except Exception as e:
        logger.error(f"Send error: {e}")


# =========================
# MAIN DETECTION LOOP
# =========================

def run_detection(token: str, camera_id: str, camera_name: str):
    fall_model, violence_model = load_models()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return

    print(f"\n✓ Webcam opened")
    print(f"✓ Camera: {camera_name}")
    print(f"✓ Clips will be saved to: {CLIPS_DIR}")
    print(f"✓ Access clips via: GET /yaqidh-api/clips/{{incident_id}}")
    print(f"✓ Press 'q' to quit\n")

    frame_buffer     = deque(maxlen=CLIP_BUFFER_MAXLEN)
    prev_frame       = None
    fall_counter     = 0
    violence_counter = 0
    frame_count      = 0
    fps_frames       = 0
    fps_actual       = 0.0
    fps_clock        = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        frame_count += 1
        fps_frames  += 1

        frame_buffer.append(frame.copy())

        # =========================
        # MOTION DETECTION
        # =========================

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)

        motion_detected = False
        motion_score    = 0

        if prev_frame is not None:
            frame_diff   = cv2.absdiff(prev_frame, gray)
            thresh       = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            motion_score = np.sum(thresh)
            if motion_score > 50000:
                motion_detected = True

        prev_frame = gray

        fall_conf         = 0.0
        violence_conf     = 0.0
        fall_detected     = False
        violence_detected = False

        # =========================
        # RUN INFERENCE
        # =========================

        if frame_count % INFERENCE_INTERVAL == 0:

            fall_results     = fall_model(frame,     imgsz=640, conf=0.4, verbose=False)
            violence_results = violence_model(frame, imgsz=640, conf=0.4, verbose=False)

            for r in fall_results:
                if r.boxes is not None:
                    boxes  = r.boxes.xyxy.cpu().numpy()
                    scores = r.boxes.conf.cpu().numpy()
                    for box, score in zip(boxes, scores):
                        x1, y1, x2, y2 = map(int, box)
                        fall_conf = max(fall_conf, float(score))
                        if score >= FALL_CONFIDENCE_THRESHOLD:
                            fall_detected = True
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(
                                frame, f"FALL {score:.2f}",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
                            )

            for r in violence_results:
                if r.boxes is not None:
                    boxes  = r.boxes.xyxy.cpu().numpy()
                    scores = r.boxes.conf.cpu().numpy()
                    for box, score in zip(boxes, scores):
                        x1, y1, x2, y2 = map(int, box)
                        violence_conf = max(violence_conf, float(score))
                        if score >= VIOLENCE_CONFIDENCE_THRESHOLD:
                            violence_detected = True
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            cv2.putText(
                                frame, f"VIOLENCE {score:.2f}",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2
                            )

            if fall_detected and motion_detected:
                fall_counter += 1
            else:
                fall_counter = 0

            if violence_detected and motion_detected:
                violence_counter += 1
            else:
                violence_counter = 0

            if fall_counter >= FALL_THRESHOLD:
                send_alert(frame, frame_buffer, camera_id, token, "fall")
                fall_counter = 0

            elif violence_counter >= VIOLENCE_THRESHOLD:
                send_alert(frame, frame_buffer, camera_id, token, "violence")
                violence_counter = 0

        # =========================
        # FPS + OVERLAY
        # =========================

        current_time = time.time()
        if current_time - fps_clock >= 1.0:
            fps_actual = fps_frames / (current_time - fps_clock)
            fps_frames = 0
            fps_clock  = current_time

        cv2.putText(frame, f"FPS: {fps_actual:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"Motion Score: {motion_score}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        cv2.putText(frame, f"Fall Counter: {fall_counter}/{FALL_THRESHOLD}",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"Violence Counter: {violence_counter}/{VIOLENCE_THRESHOLD}",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, f"Camera: {camera_name}",
                    (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Yaqidh Real-time Detection", frame)

        key = cv2.waitKey(max(1, int(1000 / FPS_LIMIT))) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\nFinished successfully!")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    token, role = login()
    camera_id, camera_name = select_camera(token, role)
    run_detection(token, camera_id, camera_name)