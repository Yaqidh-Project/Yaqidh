import os
import sys
import time
import cv2
import requests
import numpy as np
import logging
import getpass
import threading
import subprocess
from collections import deque
from pathlib import Path
from ultralytics import YOLO  

# Configure system logging parameters
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# =========================================================================
# SYSTEM APPLICATION CONFIGURATION
# =========================================================================

API_BASE_URL    = "http://127.0.0.1:8000/yaqidh-api"
REPORT_ENDPOINT = f"{API_BASE_URL}/inference/detect"

# Resolve absolute pathing strategies targeting core backend directory assets
BASE_DIR            = Path(__file__).resolve().parent.parent.parent / "backend" / "models"
FALL_MODEL_PATH     = str(BASE_DIR / "fall_detection.onnx")
VIOLENCE_MODEL_PATH = str(BASE_DIR / "violence_detection.onnx")

# Navigates up from the current file location to reach 'Backend/incident_clips'
BASE_BACKEND_DIR = Path(__file__).resolve().parents[2]
CLIPS_DIR = BASE_BACKEND_DIR / "incident_clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
# ──────────────────────────────────────────────────────────────────────────

# =========================================================================
# CAMERA VIDEO STREAM SETTINGS
# =========================================================================

FRAME_WIDTH  = 480
FRAME_HEIGHT = 360
FPS_LIMIT    = 30

CLIP_BUFFER_SECONDS = 5
CLIP_BUFFER_MAXLEN  = CLIP_BUFFER_SECONDS * FPS_LIMIT

# Drop/skip rate configuration optimized to evaluate fast-moving actions
INFERENCE_INTERVAL = 3  # Evaluates every 3 frames to avoid missing split-second falls

# =========================================================================
# ADVANCED STABLE THRESHOLDS
# =========================================================================

FALL_CONFIDENCE_THRESHOLD     = 0.7
VIOLENCE_CONFIDENCE_THRESHOLD = 0.4

# Balanced frame requirements acting against sudden spikes or false layouts
FALL_THRESHOLD     = 2  # Immediate capture for rapid fall events
VIOLENCE_THRESHOLD = 3  # Prevents fast accidental motion artifacts from triggering violence


# =========================================================================
# THREAD-SAFE SHARED MEMORY STATE DEFINITION
# =========================================================================

class SharedState:
    def __init__(self):
        self.lock            = threading.Lock()
        self.latest_frame    = None        # Tracks freshest hardware buffer frame
        self.inference_frame = None        # Isolates a locked static frame array for AI worker
        self.boxes           = []          # Stores processed boundary squares
        self.fall_counter    = 0           # Volatile index accumulators running decay tracking
        self.violence_counter = 0          # Volatile index accumulators running decay tracking
        self.motion_score    = 0           # Dynamic pixel divergence tracker tracking flow
        self.fps             = 0.0         # Calculated execution metric parameters
        self.alert_sending   = False       # Mutex block locking concurrent HTTP network calls
        self.new_frame_ready = False       # Inter-thread synchronization signaling flag


state = SharedState()


# =========================================================================
# SECURE BACKEND API AUTHENTICATION
# =========================================================================

def login() -> tuple:
    print("\n" + "="*50)
    print("  Yaqidh Real-time Detection")
    print("="*50)

    while True:
        email    = input("\nEnter email: ").strip()
        password = getpass.getpass("Enter password: ")
        try:
            r = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )
            if r.status_code == 200:
                data  = r.json()
                token = data.get("access_token")
                role  = data.get("role", "Unknown")
                logger.info(f"✓ Authenticated successfully as {email} (role: {role})")
                return token, role
            elif r.status_code == 401:
                print("✗ Invalid credentials provided. Try again.\n")
            else:
                print(f"✗ Server verification error {r.status_code} — {r.text}\n")
        except Exception as e:
            print(f"✗ Backend connection unreachable: {e}\n")


# =========================================================================
# ACTIVE HARDWARE CAMERA DISPATCH ROUTING
# =========================================================================

def select_camera(token: str, role: str) -> dict:
    """
    Fetches available cameras from the server and returns the selected camera schema data payload.
    """
    try:
        r = requests.get(
            f"{API_BASE_URL}/cameras",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code != 200:
            camera_id = input("\nEnter camera ID manually: ").strip()
            return {"camera_id": camera_id, "camera_name": "Manual", "hardware_index": 0}

        cameras = r.json()
        if not cameras:
            camera_id = input("\nNo tracking hardware discovered. Input target ID: ").strip()
            return {"camera_id": camera_id, "camera_name": "Manual", "hardware_index": 0}

        print("\nAvailable discovered streams:")
        for i, cam in enumerate(cameras, 1):
            print(f"  [{i}] {cam.get('camera_name','?')}  "
                  f"(Zone context: {cam.get('zone_id','?')})  "
                  f"Device status: {cam.get('status','?')}")
            print(f"  Ref Database ID: {cam.get('camera_id','?')}")

        while True:
            try:
                idx = int(input(f"\nSelect camera target instance [1-{len(cameras)}]: ").strip()) - 1
                if 0 <= idx < len(cameras):
                    return cameras[idx]
                print(f"  Selection index must reside between 1 and {len(cameras)}")
            except ValueError:
                print("  Provide an integer choice representation format")
    except Exception as e:
        logger.error(f"Failed handling dynamic camera selection routing: {e}")
        camera_id = input("\nEnter camera ID manually: ").strip()
        return {"camera_id": camera_id, "camera_name": "Manual", "hardware_index": 0}


# =========================================================================
# INITIALIZE AI FRAMEWORK SESSIONS
# =========================================================================

def load_models():
    logger.info("Initializing neural network graph engines...")
    fm = YOLO(FALL_MODEL_PATH,     task="detect")
    vm = YOLO(VIOLENCE_MODEL_PATH, task="detect")
    logger.info("✓ Target intelligence models mapped successfully")
    return fm, vm


# =========================================================================
# INCIDENT DISPATCHING PIPELINES & VIDEO SHAPING
# =========================================================================

def save_clip(frames: list, event_type: str) -> tuple:
    """
    Saves the buffered frames and forces a background H.264 codec re-encoding
    to guarantee full streaming playback compatibility inside browser engines.
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    temp_name = f"raw_temp_{event_type}_{ts}.mp4"
    final_name = f"{event_type}_{ts}.mp4"
    
    temp_path = CLIPS_DIR / temp_name
    final_path = CLIPS_DIR / final_name
    url = f"/incident_clips/{final_name}"
    
    # Fast container compilation via OpenCV raw writing parameters
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(temp_path), fourcc, FPS_LIMIT, (FRAME_WIDTH, FRAME_HEIGHT))
    for f in frames:
        writer.write(f)
    writer.release()
    
    cmd = [
        'ffmpeg', '-y', 
        '-i', str(temp_path), 
        '-vcodec', 'libx264', 
        '-pix_fmt', 'yuv420p', 
        '-profile:v', 'baseline', 
        '-level', '3.0', 
        '-an',  # Drops nonexistent audio channels to optimize space footprint
        str(final_path)
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if temp_path.exists():
            os.remove(temp_path)
        logger.info(f"✓ Exported web-ready H.264 incident media block: {final_path.name}")
        return str(final_path), url
    except Exception as e:
        logger.error(f"⚠️ Web transcoding processing error. Reverting to basic profile. Context: {e}")
        if temp_path.exists():
            if final_path.exists():
                os.remove(final_path)
            os.rename(temp_path, final_path)
        return str(final_path), url


def patch_clip(incident_id: str, clip_url: str, token: str):
    try:
        r = requests.patch(
            f"{API_BASE_URL}/incidents/{incident_id}",
            json={"incident_clip": clip_url},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        if r.status_code == 200:
            logger.info(f"✓ Video file reference linked into central DB context: {clip_url}")
        else:
            logger.warning(f"Database media attachment patch operation rejected: {r.status_code}")
    except Exception as e:
        logger.error(f"Network error trying to reference video inside record mapping: {e}")


def alert_worker(frame_bytes, frames_snap, camera_id, token, event_type):
    try:
        r = requests.post(
            REPORT_ENDPOINT,
            files={"frame": ("frame.jpg", frame_bytes, "image/jpeg")},
            data={"camera_id": camera_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if r.status_code != 200:
            logger.warning(f"Central alert routing pipeline rejected action payload: {r.status_code}")
            return

        result    = r.json()
        incidents = result.get("incidents") or []
        logger.info(f"✓ Alert | Incident created in DB: {result.get('incident_created', False)}")

        for inc in incidents:
            inc_id = inc.get("incident_id")
            logger.info(
                f"  ⚠️  {str(inc.get('incident_type','')).upper()} DETECTED — "
                f"ID: {inc_id} | Conf: {inc.get('confidence',0):.2f}"
            )
            if inc_id:
                _, url = save_clip(frames_snap, event_type)
                patch_clip(inc_id, url, token)
    except Exception as e:
        logger.error(f"Critical operational error managing background alert thread dispatch: {e}")
    finally:
        with state.lock:
            state.alert_sending = False


def fire_alert(frame, frame_buffer, camera_id, token, event_type):
    with state.lock:
        if state.alert_sending:
            return
        state.alert_sending = True

    frames_snap = list(frame_buffer)
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    t = threading.Thread(
        target=alert_worker,
        args=(buf.tobytes(), frames_snap, camera_id, token, event_type),
        daemon=True,
    )
    t.start()


# =========================================================================
# ASYNCHRONOUS DEEP LEARNING INFERENCE THREAD BLOCK
# =========================================================================

def inference_thread_fn(fall_model, violence_model, camera_id, token,
                        frame_buffer, stop_event):
    frame_count = 0

    FALL_LABELS     = {0: "Non fall", 1: "Fall"}
    VIOLENCE_LABELS = {0: "Non-Violence", 1: "Violence"}

    while not stop_event.is_set():
        with state.lock:
            frame = state.inference_frame
            ready = state.new_frame_ready
            if ready:
                state.new_frame_ready = False

        if not ready or frame is None:
            time.sleep(0.01)
            continue

        frame_count += 1

        fall_results     = fall_model(frame,     imgsz=640, conf=0.4, verbose=False)
        violence_results = violence_model(frame, imgsz=640, conf=0.4, verbose=False)

        new_boxes         = []
        fall_detected     = False
        violence_detected = False

        # 1. Process Fall Detection outputs
        for r in fall_results:
            if r.boxes is not None:
                for box, score, cls in zip(r.boxes.xyxy.cpu().numpy(),
                                           r.boxes.conf.cpu().numpy(),
                                           r.boxes.cls.cpu().numpy()):
                    x1, y1, x2, y2 = map(int, box)
                    class_id = int(cls)
                    label_name = FALL_LABELS.get(class_id, "Unknown")
                    
                    if label_name == "Fall":
                        if score >= FALL_CONFIDENCE_THRESHOLD:
                            fall_detected = True
                    
                    color = (0, 0, 255) if label_name == "Fall" else (0, 255, 0)
                    new_boxes.append((x1, y1, x2, y2, f"{label_name} {score:.2f}", score, color))

        # 2. Process Violence Detection outputs
        for r in violence_results:
            if r.boxes is not None:
                for box, score, cls in zip(r.boxes.xyxy.cpu().numpy(),
                                           r.boxes.conf.cpu().numpy(),
                                           r.boxes.cls.cpu().numpy()):
                    x1, y1, x2, y2 = map(int, box)
                    class_id = int(cls)
                    label_name = VIOLENCE_LABELS.get(class_id, "Unknown")
                    
                    if label_name == "Violence":
                        if score >= VIOLENCE_CONFIDENCE_THRESHOLD:
                            violence_detected = True
                    
                    color = (255, 0, 0) if label_name == "Violence" else (0, 255, 0)
                    new_boxes.append((x1, y1, x2, y2, f"{label_name} {score:.2f}", score, color))

        with state.lock:
            state.boxes = new_boxes

            if fall_detected:
                state.fall_counter += 1
            else:
                if state.fall_counter > 0:
                    state.fall_counter -= 1

            if violence_detected:
                state.violence_counter += 1
            else:
                if state.violence_counter > 0:
                    state.violence_counter -= 1

            fc = state.fall_counter
            vc = state.violence_counter
            current_frame = frame.copy()

        # Fire verified Fall alert networks
        if fc >= FALL_THRESHOLD:
            fire_alert(current_frame, frame_buffer, camera_id, token, "fall")
            with state.lock:
                state.fall_counter = 0

        # Fire verified Violence alert networks
        if vc >= VIOLENCE_THRESHOLD:
            fire_alert(current_frame, frame_buffer, camera_id, token, "violence")
            with state.lock:
                state.violence_counter = 0


# =========================================================================
# MAIN LIVE RENDERING ENGINE WINDOW LOOP
# =========================================================================

def run_detection(token: str, camera_data: dict):
    fall_model, violence_model = load_models()

    camera_id   = camera_data.get("camera_id")
    camera_name = camera_data.get("camera_name", "Unknown")
    
    if "cam2" in camera_name.lower():
        hw_index = 1
    else:
        hw_index = camera_data.get("hardware_index", 0)

    logger.info(f"Dynamically routing to database camera profile: {camera_name}")
    logger.info(f"Opening physical hardware stream index: [{hw_index}]")

    cap = cv2.VideoCapture(hw_index)
    if not cap.isOpened():
        logger.error(f"Hardware Error: Unable to interface or open webcam on index: {hw_index}")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print(f"\n✓ Stream feed matrix initialized successfully")
    print(f"✓ Camera Profile: {camera_name} (Webcam Index: {hw_index})")
    print(f"✓ Video assets mapping repository destination: {CLIPS_DIR}")
    print(f"✓ Escape keystroke listener operational: Press 'q' key to terminate tracking loop\n")

    frame_buffer = deque(maxlen=CLIP_BUFFER_MAXLEN)
    prev_gray    = None
    fps_clock    = time.time()
    fps_frames   = 0
    frame_count  = 0

    stop_event = threading.Event()
    inf_thread = threading.Thread(
        target=inference_thread_fn,
        args=(fall_model, violence_model, camera_id, token, frame_buffer, stop_event),
        daemon=True,
    )
    inf_thread.start()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        frame_count += 1
        fps_frames  += 1
        frame_buffer.append(frame.copy())

        # Rapid motion estimation matrix checking routine
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)
        motion_score = 0
        if prev_gray is not None:
            diff         = cv2.absdiff(prev_gray, gray)
            thresh       = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
            motion_score = int(np.sum(thresh))
        prev_gray = gray

        with state.lock:
            state.motion_score = motion_score

        if frame_count % INFERENCE_INTERVAL == 0:
            with state.lock:
                state.inference_frame = frame.copy()
                state.new_frame_ready = True

        with state.lock:
            boxes         = list(state.boxes)
            fall_counter  = state.fall_counter
            viol_counter  = state.violence_counter
            alert_sending = state.alert_sending

        for (x1, y1, x2, y2, label, score, color) in boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        now = time.time()
        if now - fps_clock >= 1.0:
            with state.lock:
                state.fps = fps_frames / (now - fps_clock)
            fps_frames = 0
            fps_clock  = now

        with state.lock:
            fps = state.fps

        cv2.putText(frame, f"FPS: {fps:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"Motion Score: {motion_score}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        cv2.putText(frame, f"Fall Counter: {fall_counter}/{FALL_THRESHOLD}",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"Violence Counter: {viol_counter}/{VIOLENCE_THRESHOLD}",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        if alert_sending:
            cv2.putText(frame, "Transmitting alert transaction buffers...",
                        (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.putText(frame, f"Camera Profile: {camera_name}",
                    (10, FRAME_HEIGHT - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow(f"Yaqidh Monitor: {camera_name}", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    stop_event.set()
    cap.release()
    cv2.destroyAllWindows()
    print("\nSystem streaming core processes terminated cleanly!")


# =========================================================================
# SYSTEM APPLICATION RUNTIME ENTRY POINT
# =========================================================================

if __name__ == "__main__":
    token, role = login()
    camera_data = select_camera(token, role)
    run_detection(token, camera_data)