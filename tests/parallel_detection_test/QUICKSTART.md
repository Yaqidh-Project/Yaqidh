# Quick Start Guide - Real-time Camera Testing

## 30-Second Setup

### 1. Install dependencies
```bash
pip install -r tests/requirements.txt
```

### 2. Start backend
```bash
cd Yaqidh/Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Create test user (in another terminal)
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

### 4. Create a zone and camera
```bash
# Login first to get token
TOKEN=$(curl -s -X POST "http://localhost:8000/yaqidh-api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test-password"}' | jq -r '.access_token')

# Create zone
ZONE_ID=$(curl -s -X POST "http://localhost:8000/yaqidh-api/zones" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"zone_name":"Test Zone"}' | jq -r '.zone_id')

# Assign user to zone
curl -X POST "http://localhost:8000/yaqidh-api/zones/$ZONE_ID/assign-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids":["<user-id-from-register>"]}' 

# Create camera in zone
CAMERA_ID=$(curl -s -X POST "http://localhost:8000/yaqidh-api/cameras" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"camera_name\":\"Test Camera\",\"zone_id\":\"$ZONE_ID\",\"stream_url\":\"rtsp://example.com\"}" | jq -r '.camera_id')

echo "Camera ID: $CAMERA_ID"
```

### 5. Run test script
```bash
python tests/test_realtime_camera.py

# When prompted:
# Camera ID: <paste CAMERA_ID from above>
# Email: test@example.com
# Password: test-password
```

## What You'll See

The script opens a window with your webcam feed plus these overlays:

```
FPS: 28.5
Motion Score: 0.45
Fall Counter: 0/3
Violence Counter: 0/3
Fall: 0.05
Violence: 0.15
```

Console output shows real-time detection results:

```
Sending frame 20 for inference...
============================================================
Frame #20 - Detection Results
============================================================
Fall Detection: label=no_detection, confidence=0.05
Violence Detection: label=no_detection, confidence=0.15
Incident Created: False
============================================================
```

## Testing Detection

### Simulate Fall Detection
- Quickly lower your body (squat or kneel motion)
- Watch for "Fall: X.XX" to increase
- When confidence ≥ 0.7, incident should be created with ✓ indicator

### Simulate Violence Detection
- Quick punching or hitting motions
- Watch for "Violence: X.XX" to increase
- When confidence ≥ 0.4, incident should be created with ✓ indicator

## Detection Thresholds

- **Fall**: Requires 0.7 confidence or higher
- **Violence**: Requires 0.4 confidence or higher

## Keyboard Controls

- **`q`** — Exit
- **`p`** — Pause/Resume  
- **`s`** — Save current frame

## If Something Doesn't Work

### Backend not reachable
```bash
# Check health endpoint
curl http://localhost:8000/yaqidh-api/health
```

### Authentication failed
```bash
# Verify user exists
curl -X POST "http://localhost:8000/yaqidh-api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test-password"}'
```

### Camera not found
- Make sure you created the camera via API
- Use the camera_id from the API response
- Verify the user is assigned to the camera's zone

### No detections
- Check that models are loaded: `curl http://localhost:8000/yaqidh-api/health`
- Ensure good lighting and clear visibility
- Try with clear fall/violence actions

