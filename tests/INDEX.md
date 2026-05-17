# Testing Suite - Real-time Camera Detection

Complete real-time testing and visualization system for Yaqidh AI safety detection pipeline.

## 📦 What's Included

### Core Test Script
- **`test_realtime_camera.py`** (468 lines)
  - Real-time webcam capture
  - Integration with backend `/inference/detect` endpoint
  - Fall and violence detection visualization
  - Real-time overlay with FPS, motion score, and temporal counters
  - Complete detection flow logging
  - Zone-based notification routing verification
  - WebSocket broadcast confirmation
  - Graceful exit and FPS limiting

### Documentation
- **`README.md`** — Comprehensive guide (306 lines)
  - Feature overview and architecture
  - Setup instructions and prerequisites
  - Configuration options
  - Troubleshooting guide
  - End-to-end flow diagram

- **`QUICKSTART.md`** — 30-second setup (139 lines)
  - Step-by-step rapid setup
  - Create test user and camera
  - Run test script
  - Interpret output

- **`INTEGRATION_TESTING.md`** — Detailed verification (400+ lines)
  - 12-phase verification workflow
  - Test cases for each phase
  - Performance metrics
  - Error handling guide
  - Full test coverage matrix

### Dependencies
- **`requirements.txt`** — Test dependencies
  - opencv-python (≥4.8.0)
  - requests (≥2.31.0)
  - numpy (≥1.24.0)

- **`__init__.py`** — Package initialization

## 🎯 Key Features

### Real-time Visualization
```
FPS: 28.5
Motion Score: 0.45
Fall Counter: 2/3
Violence Counter: 0/3
Fall: 0.92
Violence: 0.08
```

### Automatic Logging
- Frame-by-frame detection results
- Incident creation status
- Notification recipients
- WebSocket broadcast confirmation
- Temporal counter updates

### Backend Integration
- Uses backend detection as single source of truth
- No duplicate detection logic
- Respects cooldown rules (60 seconds)
- Verifies zone-based notification routing

### Bounding Box Drawing
- Draws boxes from backend response (not local inference)
- Labels with confidence scores
- Color-coded by detection type
- Only drawn if backend provides coordinates

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r tests/requirements.txt

# 2. Start backend
cd Yaqidh/Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Create test user (new terminal)
curl -X POST "http://localhost:8000/yaqidh-api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "test-password",
    "phone_number": "+1234567890",
    "role_name": "Teacher"
  }'

# 4. Run test script
python tests/test_realtime_camera.py
```

See `QUICKSTART.md` for full setup with camera and zone creation.

## 📋 Requirements Checklist

### ✅ Core Functionality
- [x] Open webcam using `cv2.VideoCapture(0)`
- [x] Continuously capture frames
- [x] Resize frames to 640x480
- [x] Send frames to `/inference/detect` endpoint
- [x] Print fall detection result
- [x] Print violence detection result
- [x] Print incident creation status
- [x] Print notification recipients
- [x] Print websocket broadcast status

### ✅ Visualization
- [x] Draw bounding boxes from backend response
- [x] Draw class labels
- [x] Draw confidence scores
- [x] Add FPS overlay (cv2.putText with cyan at (10,30))
- [x] Add motion score overlay (at (10,60))
- [x] Add fall counter overlay (at (10,90))
- [x] Add violence counter overlay (at (10,120))
- [x] Add fall confidence overlay (at (10,150))
- [x] Add violence confidence overlay (at (10,180))

### ✅ Debugging/Testing
- [x] Graceful exit (press 'q')
- [x] FPS limiting (30 FPS max)
- [x] Run inference every 2 frames
- [x] Calculate motion score using frame differencing
- [x] Maintain temporal verification counters
- [x] Reset counters when detection disappears
- [x] Display overlay values continuously
- [x] Log full detection flow
- [x] Log notification recipients
- [x] Log websocket broadcast status

### ✅ Architecture
- [x] No duplicate inference logic
- [x] Uses backend detection as source of truth
- [x] Respects backend cooldown (60 seconds)
- [x] Verifies zone-based notification routing
- [x] Minimal, compatible changes only

## 📁 File Structure

```
tests/
├── __init__.py                    # Package init
├── test_realtime_camera.py        # Main test script (468 lines)
├── requirements.txt               # Dependencies
├── README.md                      # Comprehensive guide (306 lines)
├── QUICKSTART.md                 # Quick start (139 lines)
├── INTEGRATION_TESTING.md         # Testing guide (400+ lines)
└── INDEX.md                       # This file
```

## 🧪 Testing Phases

The `INTEGRATION_TESTING.md` guide covers 12 verification phases:

1. **Environment Setup** — Backend and database ready
2. **Authentication** — Token acquisition and validation
3. **Real-time Capture** — Webcam and frame processing
4. **Frame Transmission** — API integration
5. **Backend Detection** — Model inference
6. **Incident Creation** — Threshold and cooldown logic
7. **Notification Routing** — Zone-based recipient selection
8. **WebSocket Broadcasting** — Event delivery
9. **Bounding Boxes** — Visual detection representation
10. **Cooldown Enforcement** — Duplicate prevention
11. **Temporal Verification** — Counter management
12. **Graceful Exit** — Cleanup and shutdown

## 🔧 Configuration

Edit constants in `test_realtime_camera.py`:

```python
API_BASE_URL = "http://localhost:8000/yaqidh-api"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
INFERENCE_INTERVAL = 2      # Run inference every N frames
FPS_LIMIT = 30
FALL_THRESHOLD = 3          # Temporal verification threshold
VIOLENCE_THRESHOLD = 3
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test-password"
```

## 🎮 Keyboard Controls

While the test script is running:

- **`q`** — Quit script
- **`p`** — Pause/Resume video
- **`s`** — Save current frame as image

## 📊 Output Example

### Console Output
```
[2024-05-17 10:30:15,234] [INFO] Starting real-time detection loop for camera 550e8400-e29b-41d4-a716-446655440000
[2024-05-17 10:30:15,234] [INFO] Press 'q' to exit, 'p' to pause/resume, 's' to save frame
[2024-05-17 10:30:16,345] [INFO] Sending frame 20 for inference...
[2024-05-17 10:30:16,876] [INFO] 
============================================================
Frame #20 - Detection Results
============================================================
Fall Detection: label=fall, confidence=0.92
Violence Detection: label=no_detection, confidence=0.08
Incident Created: True
Created Incidents (1):
  - ID: 550e8400-e29b-41d4-a716-446655440000, Category: fall, Type: fall, Confidence: 0.92
✓ Incident created - WebSocket broadcast triggered
✓ Notifications sent to zone users
  Incident 550e8400-e29b-41d4-a716-446655440000 (fall)
============================================================
```

### Visual Output
OpenCV window displays:
- Live webcam video
- FPS counter (cyan text)
- Motion score (orange text)
- Fall/violence counters (red text)
- Detection confidence scores (red text)
- Bounding boxes (red for fall, blue for violence)

## ✨ Design Philosophy

1. **Backend-centric** — Detection logic lives in backend only
2. **Visualization-focused** — Overlays are for testing/debugging
3. **Minimal scope** — Tests the full pipeline without duplication
4. **Graceful degradation** — Handles missing models, auth failures, etc.
5. **Comprehensive logging** — Verify every step of the flow

## 🚦 Next Steps

1. Follow `QUICKSTART.md` to set up and run the script
2. Use `INTEGRATION_TESTING.md` to verify each phase
3. Monitor console logs and visual output
4. Confirm all 12 phases pass
5. Deploy to production with confidence

## 📞 Support

If you encounter issues:

1. Check `README.md` Troubleshooting section
2. Review `INTEGRATION_TESTING.md` for detailed verification steps
3. Check backend health: `curl http://localhost:8000/yaqidh-api/health`
4. Verify test user: `curl -X POST http://localhost:8000/yaqidh-api/auth/login ...`

## 📝 Notes

- **Authentication required** — Script prompts for email/password
- **Zone assignment required** — User must be assigned to camera's zone
- **Cooldown enforced** — Same detection type blocked for 60 seconds
- **Temporal verification** — Counters show sequential detections
- **Motion calculation** — Frame differencing (testing/debugging only)
- **No model training** — Uses existing backend models only

---

**Created:** 2026-05-17
**Version:** 1.0.0
**Status:** Ready for testing
