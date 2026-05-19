# Real-time Camera Testing Script

This script provides real-time testing and visualization of the Yaqidh AI safety system's fall and violence detection models.

## Overview

The script:
- ✓ Opens your webcam and captures frames continuously
- ✓ Sends frames to the backend `/inference/detect` endpoint
- ✓ Displays real-time detection results with OpenCV overlays
- ✓ Logs the complete detection flow from camera to notifications
- ✓ Visualizes motion scores and temporal verification counters
- ✓ Reuses **only** backend detection results (no local YOLO inference)
- ✓ Verifies WebSocket broadcasting to zone users

## Key Design Principles

**IMPORTANT:** This script is a testing/visualization tool, not a production system.

- **Backend as Source of Truth**: All detection results come from the backend `/inference/detect` endpoint
- **No Duplicate Logic**: Motion scores, temporal counters, and visualization overlays are for testing/debugging only
- **Focused Scope**: Tests the full real-time flow without reimplementing detection pipelines

## Requirements

```bash
pip install opencv-python requests numpy
```

## Setup

### 1. Backend Prerequisites

Ensure your backend is running:

```bash
cd Yaqidh/Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API should be accessible at: `http://localhost:8000/yaqidh-api`

### 2. Create a Test User

Register a test user (or use an existing one):

```bash
curl -X POST "http://localhost:8000/yaqidh-api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "test-password",
    "phone_number": "+1234567890",
    "role_name": "Teacher"
  }'
```

### 3. Ensure Camera Exists

The test script needs a camera ID. Either:

- Create a camera via the API:
  ```bash
  curl -X POST "http://localhost:8000/yaqidh-api/cameras" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d '{
      "camera_name": "Test Camera",
      "zone_id": "<zone-id>",
      "stream_url": "rtsp://example.com/stream"
    }'
  ```

- Or provide a camera ID at runtime (the script will use it even if the camera doesn't exist in the database for this testing purpose)

## Usage

```bash
python tests/test_realtime_camera.py
```

The script will prompt for:
1. **Camera ID** (or random UUID)
2. **Email** (default: test@example.com)
3. **Password** (default: test-password)

### Controls

While the script is running:

- **`q`** — Quit
- **`p`** — Pause/Resume
- **`s`** — Save current frame

## Output

### Console Logging

The script logs the complete detection flow:

```
============================================================
Frame #10 - Detection Results
============================================================
Fall Detection: label=no_detection, confidence=0.05
Violence Detection: label=no_detection, confidence=0.15
Incident Created: False
============================================================

Frame #20 - Detection Results
============================================================
Fall Detection: label=fall, confidence=0.92
Violence Detection: label=violence, confidence=0.45
Incident Created: True
Created Incidents (2):
  - ID: 550e8400-e29b-41d4-a716-446655440000, Category: fall, Type: fall, Confidence: 0.92
  - ID: 550e8400-e29b-41d4-a716-446655440001, Category: violence, Type: violence, Confidence: 0.45
✓ Incident created - WebSocket broadcast triggered
✓ Notifications sent to zone users
  Incident 550e8400-e29b-41d4-a716-446655440000 (fall)
  Incident 550e8400-e29b-41d4-a716-446655440001 (violence)
============================================================
```

### OpenCV Display

The real-time window shows:

```
FPS: 28.5
Motion Score: 0.45
Fall Counter: 2/3
Violence Counter: 1/3
Fall: 0.92 ✓
Violence: 0.45 ✓
```

Plus bounding boxes (if backend provides box coordinates) overlaid on the video stream.

## Confidence Thresholds

The script respects backend thresholds:

- **Fall Detection**: 0.7 minimum for incident creation
  - Below 0.7: Gray text on overlay, no counter increment
  - At or above 0.7: Red text with ✓ indicator, counter increments

- **Violence Detection**: 0.4 minimum for incident creation
  - Below 0.4: Gray text on overlay, no counter increment
  - At or above 0.4: Red text with ✓ indicator, counter increments

## Verification Checklist

Use this script to verify the full detection pipeline:

### ✓ Camera Capture
- [ ] Webcam opens successfully
- [ ] Frames display smoothly
- [ ] FPS is stable

### ✓ Backend Integration
- [ ] Frames sent to `/inference/detect` endpoint
- [ ] Response parsed correctly
- [ ] Both fall and violence detection run in parallel

### ✓ Detection Accuracy
- [ ] Fall detection triggers on falls
- [ ] Violence detection triggers on violent actions
- [ ] Confidence scores reasonable
- [ ] No excessive false positives

### ✓ Incident Creation
- [ ] Fall incidents created when confidence ≥ 0.7
- [ ] Violence incidents created when confidence ≥ 0.4
- [ ] Cooldown enforced (60 seconds between same-type detections on same camera)
- [ ] Incident IDs returned in response

### ✓ Notification Flow
- [ ] Zone users identified correctly
- [ ] WebSocket broadcast message logged
- [ ] Notification recipients printed

### ✓ Visual Verification
- [ ] Motion score correlates with actual motion
- [ ] Temporal counters increment/reset appropriately
- [ ] Detection confidence displayed accurately
- [ ] Bounding boxes (if provided) correct

## Configuration

Edit these constants in the script:

```python
API_BASE_URL = "http://localhost:8000/yaqidh-api"  # Backend URL
FRAME_WIDTH = 640                                    # Resize to 640x480
FRAME_HEIGHT = 480
INFERENCE_INTERVAL = 2                              # Run inference every 2 frames
FPS_LIMIT = 30                                       # Max FPS
FALL_THRESHOLD = 3                                   # Temporal verification threshold
VIOLENCE_THRESHOLD = 3
```

## Troubleshooting

### "Cannot connect to backend"

- Ensure backend is running: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Check that the API is accessible: `curl http://localhost:8000/yaqidh-api/health`

### "Authentication failed"

- Verify test user exists: email = `test@example.com`, password = `test-password`
- Create a new user via `/auth/register`

### "Camera not found" or "Access denied"

- The test script sends a camera_id, but the backend validates that:
  1. Camera exists in the database
  2. Current user has access to that camera's zone
- Either create the camera in the database, or adjust the zone assignment

### Frames not being sent

- Check network connectivity to backend
- Ensure webcam is accessible (`ls /dev/video*` on Linux)
- Try a different camera index: `cv2.VideoCapture(1)` instead of `(0)`

### No detections

- Check that models are loaded: `curl http://localhost:8000/yaqidh-api/health`
- Verify ONNX runtime is installed and models are in `Backend/models/`
- Try with a clearer, well-lit scene

## Architecture Notes

The script demonstrates the full real-time flow:

```
┌─────────────┐
│   Webcam    │
└──────┬──────┘
       │ capture frame
       ▼
┌──────────────────────┐
│  Resize (640x480)    │
│  Calculate Motion    │
│  Update Counters     │
└──────┬───────────────┘
       │ every 2 frames
       ▼
┌──────────────────────────────────┐
│  POST /inference/detect          │
│  • camera_id                     │
│  • frame (JPEG)                  │
│  • Authorization Bearer Token    │
└──────┬───────────────────────────┘
       │
       ▼ (backend runs both models in parallel)
┌──────────────────────────────────┐
│  Backend: Fall Detection          │
│  Backend: Violence Detection      │
│  Check Confidence Threshold       │
│  Check Cooldown                   │
└──────┬───────────────────────────┘
       │
       ├─→ incident_created = true  ─→ DB: Create Incident
       │                            ─→ WS: Broadcast to zone users
       │                            ─→ Response: incident_id, type, confidence
       │
       └─→ incident_created = false ─→ Response: no incidents
       │
       ▼
┌──────────────────────────────────┐
│  Parse Response                  │
│  • fall_detection (label, conf)  │
│  • violence_detection            │
│  • incident_created              │
│  • incidents list                │
└──────┬───────────────────────────┘
       │
       ├─→ Update temporal counters
       ├─→ Draw bounding boxes (from backend)
       ├─→ Draw overlay text
       ├─→ Log detection results
       │
       ▼
┌──────────────────────────────────┐
│  Display Frame with Overlays     │
│  • FPS                           │
│  • Motion Score                  │
│  • Fall/Violence Counters        │
│  • Detection Confidence          │
│  • Bounding Boxes (if provided)  │
└──────────────────────────────────┘
```

## Development Notes

This script is intended for:
- ✓ Testing real-time detection pipeline
- ✓ Visualizing detection results
- ✓ Verifying end-to-end flow
- ✓ Debugging detection accuracy
- ✓ Monitoring notification delivery

It is **not**:
- ✗ A production deployment tool
- ✗ A model retraining system
- ✗ A replacement for unit/integration tests
- ✗ A performance benchmark tool

## Future Enhancements

Potential improvements:
- [ ] Support multiple cameras simultaneously
- [ ] Recording detected incidents
- [ ] Configurable thresholds via CLI args
- [ ] Export detection statistics
- [ ] Support for RTSP/HTTP streams in addition to webcam
- [ ] Performance profiling and bottleneck detection
