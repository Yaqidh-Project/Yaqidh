import React, { useState, useEffect } from 'react'; 
import { 
  ShieldCheck, 
  AlertOctagon, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Clock,
  Filter,
  Users,
  MapPin,
  TrendingUp
} from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center justify-between hover:shadow-md transition-shadow">
    <div>
      <p className="text-slate-500 text-sm mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-slate-800">{value}</h3>
    </div>
    <div className={`p-3 rounded-xl ${color}`}>
      <Icon size={24} className="text-white" />
    </div>
  </div>
);

export default function Dashboard() {
  const [activeFilter, setActiveFilter] = useState('all');
  const [userRole, setUserRole] = useState('User');
  const [recentActivity, setRecentActivity] = useState([]);
  
  // New States for Manager Performance Tracking
  const [performanceData, setPerformanceData] = useState(null);
  const [isLoadingPerformance, setIsLoadingPerformance] = useState(false);

  useEffect(() => {
    let role = 'manager';
    try {
      const user = JSON.parse(sessionStorage.getItem('user'));
      if (user && user.role) role = user.role.toLowerCase();
    } catch (e) {}

    const roleNames = {
      manager: 'Nursery Manager',
      teacher: 'Teacher',
      parent: 'Parent/Caregiver'
    };
    setUserRole(roleNames[role] || 'User');

    // Fetch Performance Data strictly if user is a Manager
    if (role === 'manager') {
      setIsLoadingPerformance(true);
      // Replace with your actual base URL or API utility wrapper
      fetch('/api/manager/performance-dashboard', {
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('token')}` // assuming token auth is used
        }
      })
        .then(res => res.json())
        .then(data => {
          setPerformanceData(data);
          setIsLoadingPerformance(false);
        })
        .catch(err => {
          console.error("Error loading performance tracking data:", err);
          setIsLoadingPerformance(false);
        });
    }

    // Set Role-Based Mock Data for Recent Activity Stream
    if (role === 'manager' || role === 'teacher') {
      setRecentActivity([
        { id: 1, type: 'critical', message: 'Fall Detected', time: 'Just now', details: 'Child fall detected in Playroom A' },
        { id: 2, type: 'critical', message: 'Violence Detected', time: '12 mins ago', details: 'High physical proximity detected between two children' },
        { id: 3, type: 'critical', message: 'Fall Detected', time: '2 hours ago', details: 'Child fall detected in Outdoor Playground' },
        { id: 4, type: 'warning', message: 'Violence Suspicion', time: '5 mins ago', details: 'Unusual physical interaction detected in Classroom B - needs review' }
      ]);
    } else {
      setRecentActivity([
        { id: 1, type: 'critical', message: 'Fall Detected', time: 'Just now', details: 'Activity detected in Living Room' },
        { id: 2, type: 'critical', message: 'Violence Suspicion', time: '12 mins ago', details: 'Unusual interaction in Baby\'s Bedroom' },
        { id: 3, type: 'critical', message: 'Fall Detected', time: '2 hours ago', details: 'Motion alert in Garden / Backyard' }
      ]);
    }
  }, []);

  const filteredActivity = activeFilter === 'all' 
    ? recentActivity 
    : recentActivity.filter(item => item.type === activeFilter);

  const getAlertStyle = (type) => {
    switch(type) {
      case 'critical': return 'bg-red-50 text-red-600 border-red-100';
      case 'warning': return 'bg-orange-50 text-orange-600 border-orange-100';
      case 'success': return 'bg-green-50 text-green-600 border-green-100';
      default: return 'bg-blue-50 text-blue-600 border-blue-100';
    }
  };

  // Helper to safely format average response times
  const formatResponseTime = (seconds) => {
    if (seconds === null || seconds === undefined) return "N/A";
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const remainingSecs = Math.round(seconds % 60);
    return `${mins}m ${remainingSecs}s`;
  };

  return (
    <div className="space-y-6">
      <header className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800">
          Welcome back, {userRole}
        </h2>
        <p className="text-slate-500">System Status: <span className="text-emerald-600 font-medium">Monitoring Active</span></p>
      </header>

      {/* Primary Stat Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Active Cameras" value={userRole === 'Parent/Caregiver' ? '3/3' : '4/4'} icon={ShieldCheck} color="bg-emerald-500" />
        <StatCard title="Today's Incidents" value={filteredActivity.length} icon={AlertOctagon} color="bg-rose-500" />
        {userRole === 'Nursery Manager' && (
          <StatCard 
            title="Avg Response Time" 
            value={performanceData ? formatResponseTime(performanceData.summary.nursery_average_response_time_seconds) : 'Loading...'} 
            icon={TrendingUp} 
            color="bg-indigo-500" 
          />
        )}
      </div>

      {/* MANAGER EXCLUSIVE VIEW: Routing & Performance Tracking Dashboard */}
      {userRole === 'Nursery Manager' && (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 space-y-4">
          <div className="border-b border-slate-100 pb-4">
            <h3 className="font-bold text-slate-800 text-lg flex items-center gap-2">
              <Users size={20} className="text-indigo-500" />
              Zone Routing & Teacher Performance Monitoring
            </h3>
            <p className="text-slate-500 text-sm">Monitor incident frequencies and average teacher response times across nursery zones.</p>
          </div>

          {isLoadingPerformance ? (
            <div className="text-center py-6 text-slate-400 text-sm">Fetching structural metrics matrix...</div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {performanceData?.zones_performance.map((zone) => (
                <div key={zone.zone_id} className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex flex-col justify-between space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
                        <MapPin size={16} className="text-slate-400" />
                        {zone.zone_name}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1">
                        Assigned Teacher(s): <span className="font-medium text-slate-700">{zone.assigned_teachers.join(', ') || 'Unassigned'}</span>
                      </p>
                    </div>
                    <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                      !zone.average_response_time_seconds ? 'bg-slate-200 text-slate-600' :
                      zone.average_response_time_seconds <= 60 ? 'bg-emerald-100 text-emerald-800' : 
                      zone.average_response_time_seconds <= 300 ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      Avg Delay: {formatResponseTime(zone.average_response_time_seconds)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-200/60">
                    <div className="text-slate-500">
                      Total Alerts: <span className="font-bold text-slate-700">{zone.total_incidents}</span>
                    </div>
                    <div className="text-slate-500 text-right">
                      Resolved: <span className="font-bold text-emerald-600">{zone.resolved_incidents} / {zone.total_incidents}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Activity Flow Container */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
          <h3 className="font-bold text-slate-800">Recent System Activity</h3>
          
          <div className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-xl border border-slate-100">
            {[
              { id: 'all', label: 'All', color: 'bg-white text-slate-700 shadow-sm' },
              { id: 'critical', label: 'Critical', color: 'bg-red-100 text-red-700' },
              { id: 'warning', label: 'Warnings', color: 'bg-orange-100 text-orange-700' }
            ].map((filter) => (
              <button
                key={filter.id}
                onClick={() => setActiveFilter(filter.id)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-300 ease-in-out ${
                  activeFilter === filter.id 
                    ? `${filter.color} shadow-sm scale-105` 
                    : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {filteredActivity.length > 0 ? (
            filteredActivity.map((activity) => (
              <div 
                key={activity.id} 
                className="flex items-start p-4 rounded-xl bg-slate-50 border border-slate-100 hover:bg-white hover:shadow-md transition-all duration-200 group"
              >
                <div className={`p-3 rounded-lg border ${getAlertStyle(activity.type)} mr-4 group-hover:scale-110 transition-transform`}>
                  {activity.type === 'critical' && <AlertOctagon size={20} />}
                  {activity.type === 'warning' && <AlertTriangle size={20} />}
                  {activity.type === 'success' && <CheckCircle size={20} />}
                  {activity.type === 'info' && <Info size={20} />}
                </div>

                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <h4 className="font-semibold text-slate-800 text-sm">{activity.message}</h4>
                    <div className="flex items-center text-slate-400 text-xs">
                      <Clock size={12} className="mr-1" />
                      {activity.time}
                    </div>
                  </div>
                  <p className="text-slate-500 text-sm mt-1">{activity.details}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-10 text-slate-400">
              <Filter size={48} className="mx-auto mb-3 opacity-20" />
              <p>No activities found for this filter.</p>
            </div>
          )}
        </div>
        
        <div className="mt-6 text-center pt-4 border-t border-slate-50">
          <button className="text-sm text-indigo-600 font-medium hover:text-indigo-700 hover:underline">
            View Full Incident History
          </button>
        </div>
      </div>
    </div>
  );
}