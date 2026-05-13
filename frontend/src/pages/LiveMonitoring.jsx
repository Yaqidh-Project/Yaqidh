import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Wifi, 
  Maximize2, 
  Camera,
  CameraOff,
  RefreshCw
} from 'lucide-react';

const CameraFeed = ({ name }) => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const [isStreaming, setIsStreaming] = useState(false);
  const videoRef = useRef(null);

  // Sync clock for the OSD
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Web Cam Handler - Prepared for Backend/Model Integration
  const toggleWebcam = async () => {
    if (isStreaming) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setIsStreaming(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { width: 1280, height: 720 }, 
          audio: false 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setIsStreaming(true);
        }
      } catch (err) {
        console.error("Error accessing webcam: ", err);
        alert("Could not access webcam. Please check permissions.");
      }
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden max-w-5xl mx-auto group">
      
      {/* 1. Video Feed Area */}
      <div className="relative aspect-video w-full bg-slate-950 flex items-center justify-center">
        
        {/* STANDALONE STATUS INDICATOR */}
        <div className="absolute top-4 left-4 z-20">
          {isStreaming ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-600 border border-red-400/50 shadow-lg shadow-red-900/20">
              <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
              <span className="text-[10px] font-black text-white tracking-widest uppercase">Live</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 backdrop-blur-md border border-slate-600/50">
              <div className="w-2 h-2 rounded-full bg-slate-500"></div>
              <span className="text-[10px] font-bold text-slate-300 tracking-widest uppercase">Standby</span>
            </div>
          )}
        </div>

        {/* Video Element - Model should hook into videoRef.current */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className={`w-full h-full object-cover ${!isStreaming ? 'hidden' : 'block'}`}
        />

        {/* Mockup Placeholder (Visible when cam is off) */}
        {!isStreaming && (
          <div className="flex flex-col items-center gap-4 text-slate-500">
            <div className="p-6 rounded-full bg-slate-900 border border-slate-800 shadow-inner">
              <CameraOff size={48} className="opacity-20" />
            </div>
            <p className="text-sm font-mono tracking-tighter opacity-50 uppercase">System Armed // No Signal</p>
            <button 
              onClick={toggleWebcam}
              className="mt-2 px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-full text-sm font-bold transition-all flex items-center gap-2 shadow-lg shadow-emerald-900/20"
            >
              <Camera size={16} /> Initialize Main Room
            </button>
          </div>
        )}

        {/* OSD (On-Screen Display) Metadata */}
        {isStreaming && (
          <>
            <div className="absolute top-4 right-4 z-20">
               <button className="p-2 rounded-md bg-black/40 hover:bg-black/60 text-white/80 transition-colors">
                 <Maximize2 size={16} />
               </button>
            </div>
            <div className="absolute bottom-4 right-4 font-mono text-xs text-white/80 bg-black/40 px-2 py-1 rounded backdrop-blur-sm border border-white/10">
              {new Date().toLocaleDateString()} {time}
            </div>
            <div className="absolute bottom-4 left-4 font-mono text-[10px] text-emerald-400 bg-black/40 px-2 py-1 rounded flex items-center gap-1.5 backdrop-blur-sm border border-white/10">
              <RefreshCw size={10} className="animate-spin" />
              ANALYSIS ACTIVE: 0.02ms Latency
            </div>
          </>
        )}
      </div>

      {/* 2. Controls & Metadata */}
      <div className="p-8 bg-white">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-3xl font-black text-slate-900 tracking-tight">{name}</h3>
          </div>
          
          <div className="flex items-center gap-3">
            {/* The 3-dot button was removed from here */}
            <button 
              onClick={toggleWebcam}
              className={`px-8 py-4 rounded-2xl font-bold transition-all flex items-center gap-3 shadow-sm ${
                isStreaming 
                ? 'bg-red-50 text-red-600 hover:bg-red-100' 
                : 'bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200'
              }`}
            >
              {isStreaming ? (
                <>
                  <CameraOff size={20} /> 
                  Terminate Stream
                </>
              ) : (
                <>
                  <Camera size={20} /> 
                  Power On Camera
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function LiveMonitoring() {
  return (
    <div className="min-h-screen bg-[#f8fafc] p-8 md:p-12">
      <header className="max-w-5xl mx-auto mb-10 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-emerald-600 mb-1">
            <Activity size={20} />
            <span className="text-xs font-black uppercase tracking-[0.2em]">Live Monitoring</span>
          </div>
          <h2 className="text-4xl font-black text-slate-900 tracking-tight">Main Room Feed</h2>
        </div>
        <div className="hidden md:flex items-center gap-4 text-slate-400 text-sm font-bold">
          <div className="flex items-center gap-1.5">
            <Wifi size={18} className="text-emerald-500" />
            <span className="uppercase tracking-widest">Signal: Excellent</span>
          </div>
        </div>
      </header>

      <CameraFeed name="Main Room" />
    </div>
  );
}