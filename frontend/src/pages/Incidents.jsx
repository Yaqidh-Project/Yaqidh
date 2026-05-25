import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  MapPin, 
  AlertCircle,
  Eye,
  Download,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

const IncidentCard = ({ incident, isTeacher, onViewDetails, onViewClip, onDownloadClip, onResolveIncident }) => (
  <div 
    onClick={() => onViewDetails(incident)}
    className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow cursor-pointer flex flex-col justify-between"
  >
    <div>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          {/* Card severity box wrapper matrix styling */}
          <div className={`p-3 rounded-xl ${
            incident.severity === 'critical' ? 'bg-red-100 text-red-600' : 
            incident.severity === 'warning' ? 'bg-orange-100 text-orange-600' : 
            'bg-blue-100 text-blue-600'
          }`}>
            {incident.severity === 'critical' ? <AlertTriangle size={20} /> : <AlertCircle size={20} />}
          </div>
          <div>
            <h3 className="font-semibold text-slate-800">{incident.type}</h3>
            <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
              <MapPin size={14} /> {incident.location}
            </p>
          </div>
        </div>
        
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
      
      <div className="flex items-center justify-between text-sm text-slate-600 mt-2">
        <div className="flex items-center gap-2">
          <Clock size={14} />
          <span>{incident.time}</span>
        </div>

        {/* Action controls logic blocks hidden from basic Teacher roles */}
        {!isTeacher && (
          <div className="flex items-center gap-1.5">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onViewClip(incident);
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Eye size={18} />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDownloadClip(incident);
              }}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Download size={18} />
            </button>
          </div>
        )}
      </div>
    </div>
    
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
            e.stopPropagation();
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let role = 'manager';
    try {
      const user = JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user'));
      if (user && user.role) role = user.role.toLowerCase();
    } catch (e) {
      console.error("Failed to parse user role storage nodes:", e);
    }
    
    setCurrentUserRole(role);

    // Dynamic extraction fetching live alerts from active backend API router
    axiosInstance.get('/incidents')
      .then(response => {
        const mapped = response.data.map(item => ({
          id: item.incident_id,
          type: item.incident_type,
          severity: item.danger_category === 'critical' ? 'critical' : 'warning',
          location: 'Designated Camera Scope Zone',
          time: new Date(item.timestamp).toLocaleString(),
          relativeTime: item.status === 'resolved' ? 'Archived Log' : 'Active Alert',
          status: item.status?.toLowerCase() || 'active'
        }));
        setIncidents(mapped);
        setLoading(false);
      })
      .catch(err => {
        console.error("Could not fetch database incident arrays:", err);
        setLoading(false);
      });
  }, []);

  const handleResolveIncident = (incidentId) => {
    // Triggers real-time status patch mapping to database records
    axiosInstance.patch(`/incidents/${incidentId}`, { status: 'resolved' })
      .then(() => {
        setIncidents(prev => prev.map(inc => inc.id === incidentId ? { ...inc, status: 'resolved' } : inc));
      })
      .catch(err => console.error("Database update error context logic:", err));
  };

  const activeSevere = incidents.filter(i => i.status === 'active' && i.severity === 'critical').length;
  const activeWarnings = incidents.filter(i => i.status === 'active' && i.severity === 'warning').length;
  const isTeacher = currentUserRole === 'teacher';

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex items-center justify-center font-mono text-xs text-slate-400">
        <RefreshCw className="animate-spin mr-2" size={16} /> SYNCING INCIDENTS LOG FROM DATABASE...
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <header className="mb-6">
        <h2 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
          <AlertTriangle size={32} className="text-red-500" />
          Incidents Log
        </h2>
        <p className="text-slate-500 mt-2">Track and manage all security incidents</p>
      </header>

      {/* Numerical Metrics Summary Dashboard Panel */}
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

      {/* Incidents Grid Display Panel */}
      {incidents.length === 0 ? (
        <div className="text-center py-20 text-slate-400 text-sm font-mono uppercase bg-white rounded-3xl border border-dashed border-slate-100 p-8 shadow-sm">
          ✅ No safety incidents logged inside database pipeline repository.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {incidents.map(incident => (
            <IncidentCard 
              key={incident.id} 
              incident={incident} 
              isTeacher={isTeacher}
              onViewDetails={setSelectedIncident}
              onViewClip={(inc) => console.log("Streaming Clip reference ID:", inc.id)}
              onDownloadClip={(inc) => console.log("Downloading local file reference:", inc.id)}
              onResolveIncident={handleResolveIncident}
            />
          ))}
        </div>
      )}
    </div>
  );
}