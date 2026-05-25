import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  MapPin, 
  AlertCircle,
  Eye,
  Download,
  CheckCircle2
} from 'lucide-react';

/**
 * Individual Incident Card Component
 */
const IncidentCard = ({ incident, isTeacher, onViewDetails, onViewClip, onDownloadClip, onResolveIncident }) => (
  <div 
    onClick={() => onViewDetails(incident)}
    className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between"
  >
    <div>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          {/* Icon box color logic based on severity */}
          <div className={`p-3 rounded-xl ${
            incident.severity === 'critical' ? 'bg-red-100 text-red-600' : 
            incident.severity === 'warning' ? 'bg-orange-100 text-orange-600' : 
            'bg-blue-100 text-blue-600'
          }`}>
            {incident.severity === 'critical' ? (
              <AlertTriangle size={20} />
            ) : (
              <AlertCircle size={20} />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-slate-800">{incident.type}</h3>
            <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
              <MapPin size={14} /> {incident.location}
            </p>
          </div>
        </div>
        
        {/* Right side: Severity badge and relative time */}
        <div className="flex flex-col items-end gap-1">
          <span className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
            incident.severity === 'critical' ? 'bg-red-100 text-red-600' : 
            incident.severity === 'warning' ? 'bg-orange-100 text-orange-600' : 
            'bg-blue-100 text-blue-600'
          }`}>
            {incident.severity.charAt(0).toUpperCase() + incident.severity.slice(1)}
          </span>
          
          <div className="flex items-center gap-1.5 text-slate-400 mt-1">
            <Clock size={14} />
            <span className="text-[13px] font-medium">{incident.relativeTime}</span>
          </div>
        </div>
      </div>
      
      {/* Bottom row: Absolute Timestamp & Action Icons horizontally aligned */}
      <div className="flex items-center justify-between text-sm text-slate-600 mt-2">
        <div className="flex items-center gap-2">
          <Clock size={14} />
          <span>{incident.time}</span>
        </div>

        {/* Media Actions: Completely hidden if the user is a Teacher */}
        {!isTeacher && (
          <div className="flex items-center gap-1.5">
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevents card selection trigger
                onViewClip(incident);
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors group relative"
              title="View Clip"
            >
              <Eye size={18} />
              <span className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-slate-800 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                View Clip
              </span>
            </button>
            
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevents card selection trigger
                onDownloadClip(incident);
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors group relative"
              title="Download Clip"
            >
              <Download size={18} />
              <span className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-slate-800 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                Download Clip
              </span>
            </button>
          </div>
        )}
      </div>
    </div>
    
    {/* Status Row & Teacher Functional Close Toggle Button */}
    <div className="mt-4 pt-3 border-t border-slate-50 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${incident.status === 'resolved' ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
        <span className="text-sm font-medium text-slate-600">
          {incident.status === 'resolved' ? 'Resolved' : 'Active'}
        </span>
      </div>

      {/* Show interactive close button if incident is active and current user is a Teacher */}
      {isTeacher && incident.status !== 'resolved' && (
        <button
          onClick={(e) => {
            e.stopPropagation(); // Stop background card triggers
            onResolveIncident(incident.id);
          }}
          className="flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-xl transition-all duration-200"
        >
          <CheckCircle2 size={14} />
          Mark Resolved
        </button>
      )}
    </div>
  </div>
);

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [currentUserRole, setCurrentUserRole] = useState('manager');

  useEffect(() => {
    let role = 'manager';
    try {
      const user = JSON.parse(sessionStorage.getItem('user'));
      if (user && user.role) role = user.role.toLowerCase();
    } catch (e) {
      console.error("Could not parse user role from sessionStorage", e);
    }
    
    setCurrentUserRole(role);

    if (role === 'manager' || role === 'teacher') {
      setIncidents([
        { id: 1, type: 'Fall Detected', severity: 'critical', location: 'Playroom A', time: '2026-5-13 19:00', relativeTime: 'Just now', status: 'active' },
        { id: 2, type: 'Violence Suspicion', severity: 'warning', location: 'Classroom B', time: '2026-5-13 18:40', relativeTime: '20 min ago', status: 'active' },
        { id: 3, type: 'Fall Detected', severity: 'critical', location: 'Outdoor Playground', time: '2026-5-13 18:40', relativeTime: '20 min ago', status: 'resolved' },
        { id: 4, type: 'Violence Detected', severity: 'critical', location: 'Classroom C', time: '2026-5-13 18:40', relativeTime: '20 min ago', status: 'active' },
      ]);
    } else {
      setIncidents([
        { id: 1, type: 'Fall Detected', severity: 'critical', location: "Baby's Bedroom", time: '2026-5-13 19:00', relativeTime: 'Just now', status: 'active' },
        { id: 2, type: 'Violence Suspicion', severity: 'warning', location: "Living Room", time: '2026-5-13 18:40', relativeTime: '20 min ago', status: 'active' },
        { id: 3, type: 'Fall Detected', severity: 'critical', location: 'Garden / Backyard', time: '2026-5-13 18:40', relativeTime: '20 min ago', status: 'resolved' },
      ]);
    }
  }, []);

  const handleViewClip = (incident) => {
    console.log("Viewing clip for incident:", incident.id);
  };

  const handleDownloadClip = (incident) => {
    console.log("Downloading clip for incident:", incident.id);
  };

  // Triggers the state transformation update when resolved
  const handleResolveIncident = (incidentId) => {
    // 1. Update frontend local interface visibility state
    setIncidents(prevIncidents => 
      prevIncidents.map(inc => 
        inc.id === incidentId ? { ...inc, status: 'resolved' } : inc
      )
    );

    // 2. Primed API endpoint connection wrapper
    /*
    fetch(`/api/incidents/${incidentId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionStorage.getItem('token')}`
      },
      body: JSON.stringify({ status: 'resolved' })
    })
    .then(res => res.json())
    .catch(err => console.error("Database update error:", err));
    */
    console.log(`Incident ${incidentId} marked as resolved by Teacher.`);
  };

  const activeSevere = incidents.filter(i => i.status === 'active' && i.severity === 'critical').length;
  const activeWarnings = incidents.filter(i => i.status === 'active' && i.severity === 'warning').length;
  const isTeacher = currentUserRole === 'teacher';

  return (
    <div className="space-y-6 p-4">
      <header className="mb-6">
        <h2 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
          <AlertTriangle size={32} className="text-red-500" />
          Incidents Log
        </h2>
        <p className="text-slate-500 mt-2">Track and manage all security incidents</p>
      </header>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <p className="text-slate-500 text-sm mb-2">Total Incidents</p>
          <h3 className="text-3xl font-bold text-slate-800">{incidents.length}</h3>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <p className="text-rose-600 text-sm mb-2 font-medium">Critical Alerts</p>
          <h3 className="text-3xl font-bold text-rose-600">{activeSevere}</h3>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <p className="text-orange-600 text-sm mb-2 font-medium">Warnings</p>
          <h3 className="text-3xl font-bold text-orange-600">{activeWarnings}</h3>
        </div>
      </div>

      {/* Incidents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {incidents.map(incident => (
          <IncidentCard 
            key={incident.id} 
            incident={incident} 
            isTeacher={isTeacher}
            onViewDetails={setSelectedIncident}
            onViewClip={handleViewClip}
            onDownloadClip={handleDownloadClip}
            onResolveIncident={handleResolveIncident}
          />
        ))}
      </div>
    </div>
  );
}