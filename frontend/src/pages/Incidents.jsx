import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  MapPin, 
  AlertCircle 
} from 'lucide-react';

/**
 * Individual Incident Card Component
 */
const IncidentCard = ({ incident, onViewDetails }) => (
  <div 
    onClick={() => onViewDetails(incident)}
    className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow cursor-pointer"
  >
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
    
    <div className="flex items-center gap-2 text-sm text-slate-600">
      <Clock size={14} />
      <span>{incident.time}</span>
    </div>
    
    <div className="mt-4 flex items-center gap-2">
      <div className={`w-3 h-3 rounded-full ${incident.status === 'resolved' ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <span className="text-sm font-medium text-slate-600">
        {incident.status === 'resolved' ? 'Resolved' : 'Active'}
      </span>
    </div>
  </div>
);

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    // Get user role from sessionStorage
    let role = 'manager';
    try {
      const user = JSON.parse(sessionStorage.getItem('user'));
      if (user && user.role) role = user.role;
    } catch (e) {
      console.error("Could not parse user role from sessionStorage", e);
    }

    // Set mock data based on user role
    if (role === 'manager') {
      // Manager View: Educational/Facility Locations
      setIncidents([
        { 
          id: 1, 
          type: 'Fall Detected', 
          severity: 'critical', 
          location: 'Playroom A', 
          time: '2026-5-13 19:00', 
          relativeTime: 'Just now', 
          status: 'active' 
        },
        { 
          id: 2, 
          type: 'Violence Suspicion', 
          severity: 'warning', 
          location: 'Classroom B', 
          time: '2026-5-13 18:40', 
          relativeTime: '20 min ago', 
          status: 'active' 
        },
        { 
          id: 3, 
          type: 'Fall Detected', 
          severity: 'critical', 
          location: 'Outdoor Playground', 
          time: '2026-5-13 18:40', 
          relativeTime: '20 min ago', 
          status: 'resolved' 
        },
        {
          id: 4,
          type: 'Violence Detected',
          severity: 'critical',
          location: 'Classroom C',
          time: '2026-5-13 18:40', 
          relativeTime: '20 min ago', 
          status: 'active' 
        },
      ]);
    } else {
      // Parent View: Home-based Locations
      setIncidents([
        { 
          id: 1, 
          type: 'Fall Detected', 
          severity: 'critical', 
          location: "Baby's Bedroom", 
          time: '2026-5-13 19:00', 
          relativeTime: 'Just now', 
          status: 'active' 
        },
        { 
          id: 2, 
          type: 'Violence Suspicion', 
          severity: 'warning', 
          location: "Living Room", 
          time: '2026-5-13 18:40', 
          relativeTime: '20 min ago', 
          status: 'active' 
        },
        { 
          id: 3, 
          type: 'Fall Detected', 
          severity: 'critical', 
          location: 'Garden / Backyard', 
          time: '2026-5-13 18:40', 
          relativeTime: '20 min ago', 
          status: 'resolved' 
        },
      ]);
    }
  }, []);

  // Calculate statistics for the dashboard
  const activeSevere = incidents.filter(i => i.status === 'active' && i.severity === 'critical').length;
  const activeWarnings = incidents.filter(i => i.status === 'active' && i.severity === 'warning').length;

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
          <p className="text-red-600 text-sm mb-2 font-medium">Critical Alerts</p>
          <h3 className="text-3xl font-bold text-red-600">{activeSevere}</h3>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <p className="text-orange-600 text-sm mb-2 font-medium">Warnings</p>
          <h3 className="text-3xl font-bold text-orange-600">{activeWarnings}</h3>
        </div>
      </div>

      {/* Incidents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {incidents.map(incident => (
          <IncidentCard key={incident.id} incident={incident} onViewDetails={setSelectedIncident} />
        ))}
      </div>
    </div>
  );
}