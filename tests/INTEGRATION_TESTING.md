# Integration Testing Guide

This guide explains how to verify that the real-time detection system is working end-to-end using the test script.

## Verification Workflow

### Phase 1: Environment Setup ✓

- [ ] Backend is running on `http://localhost:8000`
- [ ] PostgreSQL database is accessible
- [ ] Test user created via `/auth/register`
- [ ] Zone created and camera assigned to it
- [ ] Test user assigned to zone

**Verify**: Run `curl http://localhost:8000/yaqidh-api/health` and confirm:
```json
{
  "status": "ok",
  "fall_model_loaded": true,
  "violence_model_loaded": true,
  "active_ws_connections": 0
}
```

### Phase 2: Authentication ✓

- [ ] Test script successfully authenticates with `/auth/login`
- [ ] JWT token is received and used for subsequent requests
- [ ] Token is valid and not expired

**Verify**: When running the script:
```
[INFO] Authenticating...
[INFO] ✓ Authenticated as test@example.com
```

### Phase 3: Real-time Capture ✓

- [ ] Webcam opens successfully (no "Failed to open webcam" error)
- [ ] Frames are captured and displayed in OpenCV window
- [ ] FPS counter is visible and stable
- [ ] Motion score updates based on scene movement
- [ ] Temporal counters present in overlay

**Verify**: You should see a video window with:
```
FPS: 28.5
Motion Score: 0.45
Fall Counter: 0/3
Violence Counter: 0/3
Fall: 0.05
Violence: 0.08
```

### Phase 4: Frame Transmission ✓

- [ ] Frames are sent to `/inference/detect` endpoint
- [ ] Frames are properly formatted (JPEG, multipart form)
- [ ] Camera ID is included in request
- [ ] Authorization header is correct

**Verify**: Check console logs:
```
[INFO] Sending frame 20 for inference...
```

### Phase 5: Backend Detection ✓

- [ ] Both fall and violence detection models run in parallel
- [ ] Detection results include label and confidence
- [ ] Results are parsed correctly from response

**Verify**: Check console logs:
```
[INFO] Fall Detection: label=no_detection, confidence=0.05
[INFO] Violence Detection: label=no_detection, confidence=0.15
```

### Phase 6: Incident Creation ✓

**Test Case 1: Below Thresholds (No Incident)**
- Perform normal movements
- Fall confidence should be < 0.7
- Violence confidence should be < 0.4
- `incident_created = False`

**Test Case 2A: Fall Above Threshold (Incident Created)**
- Perform clear fall motion (squat down quickly)
- Wait for frame to be sent (every 2 frames)
- Fall confidence should be ≥ 0.7
- `incident_created = True`
- Incident ID should be generated

**Test Case 2B: Violence Above Threshold (Incident Created)**
- Perform violent motion (punching, hitting)
- Wait for frame to be sent
- Violence confidence should be ≥ 0.4
- `incident_created = True`
- Incident ID should be generated

Backend enforces:
- 60-second cooldown between same-type incidents
- Both detection types can trigger simultaneously

**Verify**: Console should show:
```
[INFO] Incident Created: True
[INFO] Created Incidents (1 or 2):
[INFO]   - ID: 550e8400-e29b-41d4-a716-446655440000, 
[INFO]     Category: fall, Type: fall, Confidence: 0.92
[INFO]   - ID: 550e8400-e29b-41d4-a716-446655440001, 
[INFO]     Category: violence, Type: violence, Confidence: 0.45
[INFO] ✓ Incident created - WebSocket broadcast triggered
```

### Phase 7: Notification Routing ✓

**Verify Zone-Based Recipients**:
- Nursery camera: Should notify admin + responsible teacher
- Home camera: Should notify parents only
- Script logs which users would receive notifications

**Verify**: Check database directly:
```sql
SELECT 
    i.incident_id,
    i.danger_category,
    c.camera_name,
    z.zone_name,
    u.full_name,
    u.role_name
FROM incidents i
JOIN cameras c ON i.camera_id = c.camera_id
JOIN zones z ON c.zone_id = z.zone_id
JOIN assigned_to atz ON z.zone_id = atz.zone_id
JOIN users u ON atz.user_id = u.user_id
WHERE i.incident_id = '<incident-id>'
ORDER BY u.full_name;
```

### Phase 8: WebSocket Broadcasting ✓

- [ ] Incident event sent via WebSocket to zone users
- [ ] Message includes all detection metadata
- [ ] Broadcasting happens synchronously with incident creation

**Verify**: Subscribe to WebSocket:
```bash
# Terminal 1: Run test script
python tests/test_realtime_camera.py

# Terminal 2: Subscribe to WebSocket
wscat -c "ws://localhost:8000/yaqidh-api/ws?token=<your-token>"

# When incident is created in Terminal 1, you should see in Terminal 2:
{
  "event": "incident_detected",
  "incident_id": "550e8400-e29b-41d4-a716-446655440000",
  "danger_category": "fall",
  "incident_type": "fall",
  "camera_id": "...",
  "confidence": 0.92,
  "timestamp": "2024-05-17T10:30:00+00:00"
}
```

### Phase 9: Bounding Boxes ✓

- [ ] If backend provides box coordinates, they are drawn
- [ ] Boxes have correct labels and confidence scores
- [ ] Overlay text is properly positioned

**Verify**: Visual inspection of video window for:
- Red boxes for fall detections
- Blue boxes for violence detections
- Labels with confidence scores

### Phase 10: Cooldown Enforcement ✓

- [ ] Same detection type on same camera blocked for 60 seconds
- [ ] Different detection types create separate incidents
- [ ] Cooldown timer resets on timeout

**Test Case**: 
1. Trigger fall detection → Incident created
2. Immediately trigger fall detection again → No new incident (cooldown)
3. Wait 60+ seconds
4. Trigger fall detection again → New incident created
5. While cooldown active, trigger violence detection → New incident (different type)

**Verify**: Console shows:
```
Frame 20 - Incident Created: True (fall)
Frame 22 - Incident Created: False (fall cooldown active)
Frame 100 - Incident Created: True (fall cooldown expired)
Frame 102 - Incident Created: True (violence created simultaneously)
```

### Phase 11: Temporal Verification ✓

- [ ] Fall counter increments when fall detected
- [ ] Violence counter increments when violence detected
- [ ] Counters reset when detection disappears

**Verify**: Overlay text shows:
```
Fall Counter: 0/3 → 1/3 → 2/3 → 3/3 (when threshold reached)
Violence Counter: 0/3 → 0/3 (when detection gone)
```

### Phase 12: Graceful Exit ✓

- [ ] Pressing 'q' exits cleanly
- [ ] Webcam is properly released
- [ ] OpenCV window closes
- [ ] No dangling processes

**Verify**:
```
[INFO] Exiting...
[INFO] Cleanup complete
```

## Performance Metrics

After running the test, you should observe:

| Metric | Target | Status |
|--------|--------|--------|
| FPS | 25-30 | ✓ |
| Frame-to-Detection Latency | < 1s | ✓ |
| Inference Time | < 500ms | ✓ |
| Motion Score Sensitivity | Responsive | ✓ |
| Memory Usage | < 500MB | ✓ |

## Error Cases

### Error: "Failed to open webcam"
- Check webcam is connected
- Try: `v4l2-ctl --list-devices` (Linux) or Device Manager (Windows)
- Use: `cv2.VideoCapture(1)` instead of `(0)` if webcam is not default

### Error: "Cannot connect to backend"
- Ensure backend is running: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Check firewall allows localhost:8000

### Error: "Authentication failed"
- Verify user exists in database
- Check credentials: email and password
- Verify user is not deactivated

### Error: "Camera not found"
- Create camera via `/cameras` API
- Verify user is assigned to camera's zone

### Error: "No detections"
- Check models are loaded: `curl http://localhost:8000/yaqidh-api/health`
- Ensure good lighting and clear visibility
- Verify ONNX models exist in `Backend/models/`

## Test Coverage Matrix

| Component | Test | Status |
|-----------|------|--------|
| **Authentication** | Login with test credentials | ✓ |
| **Webcam** | Capture and display frames | ✓ |
| **API Integration** | POST to /inference/detect | ✓ |
| **Fall Detection** | Model inference for falls | ✓ |
| **Violence Detection** | Model inference for violence | ✓ |
| **Incident Creation** | Create incident on positive detection | ✓ |
| **Cooldown** | Prevent rapid duplicate incidents | ✓ |
| **Notifications** | Send to zone users | ✓ |
| **WebSocket** | Broadcast incident events | ✓ |
| **Visualization** | Display overlays and boxes | ✓ |
| **Motion Score** | Calculate and display motion | ✓ |
| **Temporal Counters** | Track sequential detections | ✓ |

## Next Steps

If all phases pass:
1. ✓ Real-time detection pipeline is working
2. ✓ Backend models are loaded correctly
3. ✓ Notification system is functional
4. ✓ WebSocket broadcasting is active
5. ✓ Incident creation respects business rules

You can now:
- Deploy to production
- Run comprehensive integration tests
- Load test with multiple cameras
- Validate with real-world scenarios
