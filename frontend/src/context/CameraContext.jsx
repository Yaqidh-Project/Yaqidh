import React, { createContext, useContext, useState, useRef, useEffect } from 'react';
import axiosInstance from '../api/axiosInstance';

const CameraContext = createContext();
export const useCamera = () => useContext(CameraContext);

export const CameraProvider = ({ children }) => {
  const [streamingStates, setStreamingStates] = useState({});
  const [analyzingStates, setAnalyzingStates] = useState({});
  const [liveAlerts, setLiveAlerts] = useState({});

  // Core background memory retention
  const streamsRef = useRef({});
  const sessionIdsRef = useRef({});
  const wsConnectionsRef = useRef({});
  
  // Hidden background video elements to keep inference alive even if UI components unmount
  const bgVideosRef = useRef({});

  const activeCount = Object.values(streamingStates).filter(Boolean).length;

  const stopCameraPipeline = (id) => {
    if (sessionIdsRef.current[id]) sessionIdsRef.current[id] += 1;
    
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

  const spawnFrameLoop = (id, currentSessionId, name) => {
    const runLoop = () => {
      if (currentSessionId !== sessionIdsRef.current[id] || !streamsRef.current[id] || !streamsRef.current[id].active) {
        return;
      }

      const video = bgVideosRef.current[id];
      if (!video || video.paused || video.ended) {
        setTimeout(runLoop, 300);
        return;
      }

      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 480;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        setTimeout(runLoop, 300);
        return;
      }

      try {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      } catch (e) {
        setTimeout(runLoop, 300);
        return;
      }

      canvas.toBlob(async (blob) => {
        if (currentSessionId !== sessionIdsRef.current[id] || !blob) return;

        const formData = new FormData();
        formData.append('camera_id', id);
        formData.append('frame', blob, `live_frame_${id}.jpg`);

        try {
          setAnalyzingStates(prev => ({ ...prev, [id]: true }));
          const response = await axiosInstance.post('/inference/detect', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });

          if (currentSessionId !== sessionIdsRef.current[id]) return;
          setAnalyzingStates(prev => ({ ...prev, [id]: false }));

          const { incident_created, incidents } = response.data;
          if (incident_created && incidents && incidents.length > 0) {
            const detectedEvent = incidents[0];
            const confidence = (detectedEvent.confidence * 100).toFixed(0);
            
            setLiveAlerts(prev => ({ 
              ...prev, 
              [id]: `⚠️ CRITICAL HTTP: ${detectedEvent.incident_type.toUpperCase()} DETECTED inside ${name} (${confidence}%)` 
            }));
            setTimeout(() => {
              if (currentSessionId === sessionIdsRef.current[id]) {
                setLiveAlerts(prev => ({ ...prev, [id]: null }));
              }
            }, 4000);
          }
        } catch (err) {
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
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      let constraints = { video: { width: 1280, height: 720 }, audio: false };

      if (videoDevices.length > 0) {
        if (index === 0) {
          const builtInCam = videoDevices.find(d => d.label.toLowerCase().includes('integrated') || d.label.toLowerCase().includes('built-in'));
          constraints.video.deviceId = builtInCam ? { exact: builtInCam.deviceId } : { exact: videoDevices[0].deviceId };
        } else {
          const targetIndex = index < videoDevices.length ? index : videoDevices.length - 1;
          constraints.video.deviceId = { exact: videoDevices[targetIndex].deviceId };
        }
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamsRef.current[id] = stream;

      // Create a persistent hidden background video player to bypass DOM unmounting drops
      const bgVideo = document.createElement('video');
      bgVideo.setAttribute('autoplay', 'true');
      bgVideo.setAttribute('playsinline', 'true');
      bgVideo.muted = true;
      bgVideo.srcObject = stream;
      bgVideosRef.current[id] = bgVideo;
      
      // Play background video to keep frames active
      await bgVideo.play();

      if (uiVideoElement) {
        uiVideoElement.srcObject = stream;
      }

      setStreamingStates(prev => ({ ...prev, [id]: true }));
      localStorage.setItem(`camera_active_${id}`, 'true');
      
      // Run the persistent frame loop tied straight to the background video stream
      spawnFrameLoop(id, freshSessionId, name);

      const token = localStorage.getItem('token');
      const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/notifications?token=${token}`;
      const ws = new WebSocket(wsUrl);
      wsConnectionsRef.current[id] = ws;

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (freshSessionId === sessionIdsRef.current[id] && data.camera_id === id && (data.event === "incident_detected" || data.event === "incident_created")) {
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
    <CameraContext.Provider value={{
      streamingStates,
      analyzingStates,
      liveAlerts,
      streamsRef,
      activeCount,
      startCameraPipeline,
      stopCameraPipeline
    }}>
      {children}
    </CameraContext.Provider>
  );
};