import React, { createContext, useContext, useState, useRef } from 'react';
import axiosInstance from '../api/axiosInstance';

const CameraContext = createContext();
export const useCamera = () => useContext(CameraContext);

export const CameraProvider = ({ children }) => {
  const [streamingStates, setStreamingStates] = useState({});
  const [analyzingStates, setAnalyzingStates] = useState({});
  const [liveAlerts, setLiveAlerts] = useState({});

  const streamsRef = useRef({});
  const sessionIdsRef = useRef({});
  const wsConnectionsRef = useRef({});
  const bgVideosRef = useRef({});

  const mediaRecordersRef = useRef({});
  const recordedChunksRef = useRef({});

  const activeCount = Object.values(streamingStates).filter(Boolean).length;

  const stopCameraPipeline = (id) => {
    if (sessionIdsRef.current[id]) {
      sessionIdsRef.current[id] += 1;
    }

    if (mediaRecordersRef.current[id]) {
      try { mediaRecordersRef.current[id].stop(); } catch (e) {}
      delete mediaRecordersRef.current[id];
    }
    delete recordedChunksRef.current[id];

    if (streamsRef.current[id]) {
      streamsRef.current[id].getTracks().forEach(track => track.stop());
      delete streamsRef.current[id];
    }

    if (wsConnectionsRef.current[id]) {
      wsConnectionsRef.current[id].close();
      delete wsConnectionsRef.current[id];
    }

    if (bgVideosRef.current[id]) {
      bgVideosRef.current[id].srcObject = null;
      bgVideosRef.current[id].remove();
      delete bgVideosRef.current[id];
    }

    setStreamingStates(prev => ({ ...prev, [id]: false }));
    setAnalyzingStates(prev => ({ ...prev, [id]: false }));
    setLiveAlerts(prev => ({ ...prev, [id]: null }));
    localStorage.setItem(`camera_active_${id}`, 'false');
  };

  /**
   * Returns a Promise that resolves with a finalized video Blob.
   *
   * Strategy: stop the current recorder (which flushes all buffered data and
   * fires the final `dataavailable` event), collect the result, then
   * immediately spin up a fresh recorder so the next cycle has clean chunks.
   *
   * MIN_CHUNKS: wait until at least this many 500ms slices are buffered
   * before harvesting, giving ~3 seconds of footage minimum.
   */
  const MIN_CHUNKS = 3; // 3 × 500 ms = ~1.5 seconds

  const _harvestClip = (id) => {
    return new Promise((resolve) => {
      const recorder = mediaRecordersRef.current[id];
      const stream   = streamsRef.current[id];

      if (!recorder || recorder.state === 'inactive' || !stream) {
        resolve(null);
        return;
      }

      // Not enough footage yet — skip this cycle, keep recording
      if ((recordedChunksRef.current[id] || []).length < MIN_CHUNKS) {
        resolve(null);
        return;
      }

      // Collect whatever is already buffered
      const existingChunks = [...(recordedChunksRef.current[id] || [])];

      // Listen for the final chunk that arrives when we call .stop()
      const onStop = () => {
        recorder.removeEventListener('stop', onStop);

        const allChunks = [...existingChunks, ...(recordedChunksRef.current[id] || [])];

        if (allChunks.length === 0) {
          resolve(null);
        } else {
          resolve(new Blob(allChunks, { type: 'video/webm' }));
        }

        // ── Restart a fresh recorder immediately ──────────────────────────
        try {
          recordedChunksRef.current[id] = [];
          const fresh = new MediaRecorder(stream, { mimeType: 'video/webm' });

          fresh.ondataavailable = (e) => {
            if (e.data.size > 0) {
              recordedChunksRef.current[id] = recordedChunksRef.current[id] || [];
              recordedChunksRef.current[id].push(e.data);
              // Keep a rolling ~20-second window (1 chunk/s × 20)
              if (recordedChunksRef.current[id].length > 20) {
                recordedChunksRef.current[id].shift();
              }
            }
          };

          fresh.start(500); // 500 ms slices → ~3 s minimum before next harvest
          mediaRecordersRef.current[id] = fresh;
        } catch (e) {
          console.warn('Could not restart MediaRecorder:', e);
        }
      };

      recorder.addEventListener('stop', onStop);

      // Grab any data buffered since the last timeslice, then stop
      try {
        recorder.requestData(); // flush current buffer → ondataavailable fires
        recorder.stop();        // triggers final dataavailable + stop events
      } catch (e) {
        recorder.removeEventListener('stop', onStop);
        resolve(null);
      }
    });
  };

  const spawnFrameLoop = (id, currentSessionId, name) => {
    const runLoop = async () => {
      if (
        currentSessionId !== sessionIdsRef.current[id] ||
        !streamsRef.current[id] ||
        !streamsRef.current[id].active
      ) return;

      const video = bgVideosRef.current[id];
      if (!video || video.paused || video.ended) {
        setTimeout(runLoop, 300);
        return;
      }

      const canvas = document.createElement('canvas');
      canvas.width  = 640;
      canvas.height = 480;
      const ctx = canvas.getContext('2d');
      if (!ctx) { setTimeout(runLoop, 300); return; }

      try {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      } catch (e) {
        setTimeout(runLoop, 300);
        return;
      }

      canvas.toBlob(async (frameBlob) => {
        if (currentSessionId !== sessionIdsRef.current[id] || !frameBlob) return;

        // ── Harvest a finalized clip before building the request ──────────
        const clipBlob = await _harvestClip(id);

        if (currentSessionId !== sessionIdsRef.current[id]) return;

        const formData = new FormData();
        formData.append('camera_id', id);
        formData.append('frame', frameBlob, `live_frame_${id}.jpg`);

        if (clipBlob && clipBlob.size > 0) {
          // Explicit filename + MIME type so the backend sees video/webm
          formData.append('clip', clipBlob, `incident_${id}.webm`);
        }

        try {
          setAnalyzingStates(prev => ({ ...prev, [id]: true }));

          const response = await axiosInstance.post(
            '/inference/detect',
            formData,
            { headers: { 'Content-Type': 'multipart/form-data' } }
          );

          if (currentSessionId !== sessionIdsRef.current[id]) return;

          setAnalyzingStates(prev => ({ ...prev, [id]: false }));

          const { incident_created, incidents } = response.data;

          if (incident_created && incidents && incidents.length > 0) {
            const detectedEvent = incidents[0];
            const confidence = (detectedEvent.confidence * 100).toFixed(0);

            setLiveAlerts(prev => ({
              ...prev,
              [id]:
                `⚠️ CRITICAL HTTP: ` +
                `${detectedEvent.incident_type.toUpperCase()} ` +
                `DETECTED inside ${name} (${confidence}%)`
            }));

            setTimeout(() => {
              if (currentSessionId === sessionIdsRef.current[id]) {
                setLiveAlerts(prev => ({ ...prev, [id]: null }));
              }
            }, 4000);
          }
        } catch (err) {
          console.error('Inference error:', err);
          if (currentSessionId === sessionIdsRef.current[id]) {
            setAnalyzingStates(prev => ({ ...prev, [id]: false }));
          }
        }

        if (currentSessionId === sessionIdsRef.current[id]) {
          setTimeout(runLoop, 300);
        }
      }, 'image/jpeg', 0.7);
    };

    setTimeout(runLoop, 300);
  };

  const startCameraPipeline = async (id, name, index, uiVideoElement) => {
    try {
      if (!sessionIdsRef.current[id]) sessionIdsRef.current[id] = 0;
      sessionIdsRef.current[id] += 1;
      const freshSessionId = sessionIdsRef.current[id];

      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(d => d.kind === 'videoinput');

      let constraints = { video: { width: 1280, height: 720 }, audio: false };

      if (videoDevices.length > 0) {
        if (index === 0) {
          const builtInCam = videoDevices.find(
            d =>
              d.label.toLowerCase().includes('integrated') ||
              d.label.toLowerCase().includes('built-in')
          );
          constraints.video.deviceId = builtInCam
            ? { exact: builtInCam.deviceId }
            : { exact: videoDevices[0].deviceId };
        } else {
          const targetIndex = index < videoDevices.length ? index : videoDevices.length - 1;
          constraints.video.deviceId = { exact: videoDevices[targetIndex].deviceId };
        }
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamsRef.current[id] = stream;

      // Hidden background video for canvas capture
      const bgVideo = document.createElement('video');
      bgVideo.setAttribute('autoplay', 'true');
      bgVideo.setAttribute('playsinline', 'true');
      bgVideo.muted    = true;
      bgVideo.srcObject = stream;
      bgVideosRef.current[id] = bgVideo;
      await bgVideo.play();

      // ── MediaRecorder: 1-second timeslices, rolling 20-chunk buffer ───────
      recordedChunksRef.current[id] = [];
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current[id].push(event.data);
          if (recordedChunksRef.current[id].length > 20) {
            recordedChunksRef.current[id].shift();
          }
        }
      };

      mediaRecorder.start(500); // 500 ms slices → ~3 s minimum before next harvest
      mediaRecordersRef.current[id] = mediaRecorder;

      if (uiVideoElement) uiVideoElement.srcObject = stream;

      setStreamingStates(prev => ({ ...prev, [id]: true }));
      localStorage.setItem(`camera_active_${id}`, 'true');

      spawnFrameLoop(id, freshSessionId, name);

      // ── WebSocket for server-push incident notifications ──────────────────
      const token = localStorage.getItem('token');
      const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/notifications?token=${token}`;
      const ws    = new WebSocket(wsUrl);
      wsConnectionsRef.current[id] = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (
          freshSessionId === sessionIdsRef.current[id] &&
          data.camera_id === id &&
          (data.event === 'incident_detected' || data.event === 'incident_created')
        ) {
          setLiveAlerts(prev => ({
            ...prev,
            [id]: `⚠️ DB RECORDED: ${data.incident_type.toUpperCase()} alert tracked inside ${name}!`
          }));

          setTimeout(() => {
            if (freshSessionId === sessionIdsRef.current[id]) {
              setLiveAlerts(prev => ({ ...prev, [id]: null }));
            }
          }, 5000);
        }
      };
    } catch (err) {
      console.error(`Error activating media layers for ${name}:`, err);
    }
  };

  return (
    <CameraContext.Provider
      value={{
        streamingStates,
        analyzingStates,
        liveAlerts,
        streamsRef,
        activeCount,
        startCameraPipeline,
        stopCameraPipeline,
      }}
    >
      {children}
    </CameraContext.Provider>
  );
};