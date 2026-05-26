import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Maximize2, 
  Camera,
  CameraOff,
  RefreshCw,
  LayoutGrid,
  Square
} from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

/**
 * CameraFeed Component
 * Captures live hardware video tracks and streams lightweight compressed JPEG frames
 * to the backend YOLOv8 ONNX pipeline sequentially for instant drop-down risk detection.
 */
const CameraFeed = ({ id, name, index }) => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const [isStreaming, setIsStreaming] = useState(false);
  const [liveAlert, setLiveAlert] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  
  // FIXED: Using a strict numeric session ID to completely invalidate cloned/ghost background intervals
  const streamSessionIdRef = useRef(0);

  // Synchronize internal UI digital clock representation
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  /**
   * ABSOLUTE HARD TEARDOWN ON UNMOUNT
   * Enforces zero background activity when Aliyah leaves the monitoring page.
   */
  useEffect(() => {
    return () => {
      // Incrementing the ID instantly invalidates any currently running async intervals in browser memory
      streamSessionIdRef.current += 1;
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  /**
   * Safe teardown mechanism for manual stream termination via the UI toggle button
   */
  const stopInferencePipeline = () => {
    // HARD LOCK: Invalidate the current session ID instantly to block all running background callbacks
    streamSessionIdRef.current += 1;

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setIsAnalyzing(false);
    setLiveAlert(null);
  };

  /**
   * Frame Capture Matrix Engine
   * Orchestrates the active snapshot loop. Injected with a local state validation token
   * to immediately self-destruct if the parent camera feed was terminated.
   */
  const spawnFrameInferenceLoop = (currentSessionId) => {
    const runLoop = () => {
      // STRICT LIFECYCLE CHECK: If the session ID changed, suicide this loop context immediately!
      if (currentSessionId !== streamSessionIdRef.current || !videoRef.current || !streamRef.current || !streamRef.current.active) {
        return;
      }

      const video = videoRef.current;
      if (video.paused || video.ended) {
        // Schedule next execution window if momentarily paused
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
        return; // Guard against frame buffer locks
      }
      
      canvas.toBlob(async (blob) => {
        // RE-VERIFY TOKEN: Ensure camera wasn't killed during async compression processing time
        if (currentSessionId !== streamSessionIdRef.current || !blob) return;
        
        const formData = new FormData();
        formData.append('camera_id', id);
        formData.append('frame', blob, `live_frame_${id}.jpg`);

        try {
          setIsAnalyzing(true);
          const response = await axiosInstance.post('/inference/detect', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });

          // FINAL CONTEXT VERIFICATION: Drop response UI mutations if session has been closed
          if (currentSessionId !== streamSessionIdRef.current) return;

          const { incident_created, incidents } = response.data;
          setIsAnalyzing(false);

          if (incident_created && incidents && incidents.length > 0) {
            const detectedEvent = incidents[0];
            const labelName = detectedEvent.incident_type.toUpperCase();
            const confidence = (detectedEvent.confidence * 100).toFixed(0);
            
            setLiveAlert(`⚠️ CRITICAL HTTP: ${labelName} DETECTED inside ${name} (${confidence}% Confidence)`);
            setTimeout(() => {
              if (currentSessionId === streamSessionIdRef.current) setLiveAlert(null);
            }, 4000);
          }
        } catch (err) {
          if (currentSessionId === streamSessionIdRef.current) {
            console.error(`Network frame processing dropped for camera ${name}:`, err);
            setIsAnalyzing(false);
          }
        }

        // Recursively trigger the next frame sample capture only if this session context remains alive
        if (currentSessionId === streamSessionIdRef.current) {
          setTimeout(runLoop, 300);
        }
      }, 'image/jpeg', 0.7);
    };

    // Trigger initial loop instantiation pass
    setTimeout(runLoop, 300);
  };

  /**
   * Hardware Media Device Negotiation Routing Engine
   */
  const toggleWebcam = async () => {
    if (!id || id.includes('placeholder')) {
      alert("No active camera hardware pipeline detected for this zone framework.");
      return;
    }

    if (isStreaming) {
      stopInferencePipeline();
    } else {
      try {
        // Invalidate any trailing legacy loops by shifting the session ID boundary forward
        streamSessionIdRef.current += 1;
        const freshSessionId = streamSessionIdRef.current;

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
        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setIsStreaming(true);

          // INJECT CURRENT SESSION ID: Tethers the recursive loop straight to this operational life window
          spawnFrameInferenceLoop(freshSessionId);
        }

        const token = localStorage.getItem('token');
        const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/notifications?token=${token}`;
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (freshSessionId === streamSessionIdRef.current && ((data.event === "incident_detected" || data.event === "incident_created") && data.camera_id === id)) {
            setLiveAlert(`⚠️ DB RECORDED: ${data.incident_type.toUpperCase()} alert tracked inside ${name}!`);
            setTimeout(() => {
              if (freshSessionId === streamSessionIdRef.current) setLiveAlert(null);
            }, 5000); 
          }
        };

      } catch (err) {
        console.error(`Error activating media layout stream layers for ${name}:`, err);
        alert(`Could not initialize camera pipeline for ${name}. Verify system permissions.`);
      }
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden w-full group transition-all duration-300">
      <div className="relative aspect-video w-full bg-slate-950 flex items-center justify-center">
        
        {liveAlert && (
          <div className="absolute top-16 left-4 right-4 z-30 p-4 bg-red-600 text-white rounded-xl text-center font-bold text-sm animate-bounce shadow-xl">
            {liveAlert}
          </div>
        )}

        <div className="absolute top-4 left-4 z-20">
          {isStreaming ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-600 border border-red-400/50 shadow-lg shadow-red-900/20">
              <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
              <span className="text-[10px] font-black text-white tracking-widest uppercase">Live Stream</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 backdrop-blur-md border border-slate-600/50">
              <div className="w-2 h-2 rounded-full bg-slate-500"></div>
              <span className="text-[10px] font-bold text-slate-300 tracking-widest uppercase">Standby</span>
            </div>
          )}
        </div>

        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${!isStreaming ? 'hidden' : 'block'}`}
        />

        {!isStreaming && (
          <div className="flex flex-col items-center gap-4 text-slate-500 p-4 text-center">
            <div className="p-4 rounded-full bg-slate-900 border border-slate-800 shadow-inner">
              <CameraOff size={32} className="opacity-20" />
            </div>
            <p className="text-xs font-mono tracking-tighter opacity-50 uppercase">System Armed // Stream Offline</p>
            <button 
              onClick={toggleWebcam}
              className="mt-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-full text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-emerald-900/20"
            >
              <Camera size={14} /> Power On Feed
            </button>
          </div>
        )}

        {isStreaming && (
          <>
            <div className="absolute top-4 right-4 z-20">
               <button className="p-2 rounded-md bg-black/40 hover:bg-black/60 text-white/80 transition-colors">
                 <Maximize2 size={14} />
               </button>
            </div>
            <div className="absolute bottom-4 right-4 font-mono text-[10px] text-white/80 bg-black/40 px-2 py-1 rounded backdrop-blur-sm border border-white/10">
              {new Date().toLocaleDateString()} {time}
            </div>
            <div className="absolute bottom-4 left-4 font-mono text-[9px] text-emerald-400 bg-black/40 px-2 py-1 rounded flex items-center gap-1.5 backdrop-blur-sm border border-white/10">
              <RefreshCw size={10} className={isAnalyzing ? "animate-spin" : ""} />
              {isAnalyzing ? "AI SYSTEM: TRANSMITTING PARALLEL FRAME SEGMENT..." : "AI SYSTEM: REAL-TIME THREAT SCANNING ACTIVE"}
            </div>
          </>
        )}
      </div>

      <div className="p-4 bg-white border-t border-slate-100">
        <div className="flex justify-between items-center gap-4">
          <div>
            <h4 className="text-lg font-bold text-slate-900 truncate">{name}</h4>
          </div>
          <button 
            onClick={toggleWebcam}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap ${
              isStreaming ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-slate-900 text-white hover:bg-slate-800'
            }`}
          >
            {isStreaming ? (
              <><CameraOff size={14} /> Terminate</>
            ) : (
              <><Camera size={14} /> Power On</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Main Layout Dashboard Root Module
 */
export default function LiveMonitoring() {
  const [cameras, setCameras] = useState([]);
  const [viewMode, setViewMode] = useState('all'); 
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axiosInstance.get('/cameras') 
      .then(response => {
        const formattedCameras = response.data.map(cam => ({
          id: cam.camera_id,
          name: cam.name || cam.camera_name || 'Active Room Feed'
        }));
        setCameras(formattedCameras);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to sync camera tree data structures:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex items-center justify-center font-mono text-xs text-slate-400">
        <RefreshCw className="animate-spin mr-2" size={16} /> INITIALIZING AI PIPELINE FEEDS...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 md:p-12">
      <header className="max-w-7xl mx-auto mb-10 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 border-b border-slate-200/60 pb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-600 mb-1">
            <Activity size={20} />
            <span className="text-xs font-black uppercase tracking-[0.2em]">Live Safety Scanning</span>
          </div>
          <h2 className="text-4xl font-black text-slate-900 tracking-tight">Live Camera Panel</h2>
        </div>
        
        {cameras.length > 1 && (
          <div className="flex items-center gap-2 bg-white p-1.5 rounded-2xl border border-slate-200 shadow-sm flex-wrap">
            <button
              onClick={() => setViewMode('all')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                viewMode === 'all' ? 'bg-brand-500 text-white shadow-md' : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <LayoutGrid size={16} /> Split View ({cameras.length})
            </button>
            
            {cameras.map(cam => (
              <button
                key={cam.id}
                onClick={() => setViewMode(cam.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  viewMode === cam.id ? 'bg-brand-500 text-white shadow-md' : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Square size={16} /> {cam.name}
              </button>
            ))}
          </div>
        )}
      </header>

      <main className="max-w-7xl mx-auto">
        {cameras.length === 0 ? (
          <div className="text-center py-20 text-slate-400 text-sm font-mono uppercase tracking-wider bg-white rounded-3xl border border-dashed border-slate-200 p-8 shadow-sm">
            ⚠️ No active cameras registered for this account zone framework.
          </div>
        ) : (
          <div className={`grid gap-8 transition-all duration-500 ${
            viewMode === 'all' && cameras.length > 1 ? 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1 max-w-4xl mx-auto'
          }`}>
            {cameras
              .filter(cam => viewMode === 'all' || viewMode === cam.id)
              .map((cam, idx) => (
                <CameraFeed key={cam.id} id={cam.id} name={cam.name} index={idx} />
              ))
            }
          </div>
        )}
      </main>
    </div>
  );
}