import React, { useState, useEffect } from 'react';
import { User, Bell, Camera, Users, Upload, Plus, Edit2, Trash2, RefreshCw } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

const TabButton = ({ tab, activeTab, onClick, label }) => (
  <button
    onClick={() => onClick(tab)}
    className={`px-4 py-3 rounded-xl font-medium transition duration-200 ${
      activeTab === tab ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-100'
    }`}
  >
    {label}
  </button>
);

// Tab 1: Edit Profile (Dynamic Binding)
const EditProfile = () => {
  const [profileData, setProfileData] = useState({ name: '', email: '', phone: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetches account details from backend dependency injectors
    axiosInstance.get('/users/me')
      .then(res => {
        setProfileData({
          name: res.data.full_name || '',
          email: res.data.email || '',
          phone: res.data.phone_number || ''
        });
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading account profiles:", err);
        setLoading(false);
      });
  }, []);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = () => {
    axiosInstance.patch('/users/me', {
      full_name: profileData.name,
      phone_number: profileData.phone
    })
    .then(() => alert("Profile information securely committed."))
    .catch(err => console.error("Failed to commit profile updates:", err));
  };

  if (loading) return <div className="text-slate-400 font-mono text-xs py-4">LOADING ACCOUNT INFORMATION...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-semibold text-slate-800 mb-6">Profile Information</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Full Name</label>
            <input
              type="text"
              name="name"
              value={profileData.name}
              onChange={handleProfileChange}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Email Address</label>
            <input
              type="email"
              name="email"
              value={profileData.email}
              disabled
              className="w-full px-4 py-3 border border-slate-200 rounded-xl bg-slate-50 text-slate-400 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={profileData.phone}
              onChange={handleProfileChange}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>
        <button onClick={handleSave} className="mt-6 w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3 rounded-xl transition">
          Save Changes
        </button>
      </div>
    </div>
  );
};

// Tab 2: Notifications (Removed SMS Per Project Specifications)
const NotificationsTab = () => {
  const [notifications, setNotifications] = useState({
    email: true,
    app: true,
    dashboardIndicators: true,
  });

  const toggleNotification = (key) => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-semibold text-slate-800 mb-6">Notification Channels</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition">
            <div>
              <p className="font-medium text-slate-800">Email Notifications</p>
              <p className="text-sm text-slate-500">Receive structural safety alerts via validated emails</p>
            </div>
            <button
              onClick={() => toggleNotification('email')}
              className={`px-4 py-2 rounded-xl font-medium text-sm transition ${
                notifications.email ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
              }`}
            >
              {notifications.email ? 'On' : 'Off'}
            </button>
          </div>

          <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition">
            <div>
              <p className="font-medium text-slate-800">Mobile Push System</p>
              <p className="text-sm text-slate-500">Receive real-time persistent hardware push signals</p>
            </div>
            <button
              onClick={() => toggleNotification('app')}
              className={`px-4 py-2 rounded-xl font-medium text-sm transition ${
                notifications.app ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
              }`}
            >
              {notifications.app ? 'On' : 'Off'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Tab 3: Manage Cameras (Dynamic Persistence Mapped to Databases)
const ManageCameras = ({ role }) => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', ip: '', zone_id: '', status: 'Online' });
  const [zones, setZones] = useState([]);

  const fetchCamerasAndZones = () => {
    setLoading(true);
    // Concurrent request tracking matrix maps zones alongside assigned cameras
    Promise.all([axiosInstance.get('/cameras'), axiosInstance.get('/zones')])
      .then(([camRes, zoneRes]) => {
        setCameras(camRes.data);
        setZones(zoneRes.data);
        setLoading(false)
      })
      .catch(err => {
        console.error("Database tracking extraction failure:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCamerasAndZones();
  }, []);

  const handleAddCamera = () => {
    if (editingId) {
      axiosInstance.patch(`/cameras/${editingId}`, { camera_name: formData.name, ip_address: formData.ip })
        .then(() => {
          fetchCamerasAndZones();
          setShowForm(false);
          setEditingId(null);
        });
    } else {
      axiosInstance.post('/cameras', { camera_name: formData.name, ip_address: formData.ip, zone_id: formData.zone_id })
        .then(() => {
          fetchCamerasAndZones();
          setShowForm(false);
        });
    }
  };

  const handleDelete = (id) => {
    if(window.confirm("Confirm permanent hardware camera mapping deletion?")) {
      axiosInstance.delete(`/cameras/${id}`).then(() => fetchCamerasAndZones());
    }
  };

  if (loading) return <div className="text-slate-400 font-mono text-xs py-4">LOADING CAMERAS CONFIGURATIONS...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-slate-800">
          {role === 'manager' ? 'Nursery Camera Topology' : 'Home Infrastructure System'}
        </h3>
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2">
          <Plus size={20} /> Add Camera
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-4">
          <input
            placeholder="Camera Reference Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none"
          />
          <input
            placeholder="Hardware Static IP Address"
            value={formData.ip}
            onChange={(e) => setFormData({...formData, ip: e.target.value})}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none"
          />
          <select
            value={formData.zone_id}
            onChange={(e) => setFormData({...formData, zone_id: e.target.value})}
            className="w-full px-4 py-3 border border-slate-200 rounded-xl bg-white"
          >
            <option value="">Select Target Deployment Zone Location</option>
            {zones.map(z => <option key={z.zone_id} value={z.zone_id}>{z.zone_name}</option>)}
          </select>
          <div className="flex gap-2">
            <button onClick={handleAddCamera} className="px-4 py-2 bg-brand-500 text-white rounded-xl">Commit</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-slate-200 rounded-xl">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cameras.map(camera => (
          <div key={camera.camera_id} className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
            <div>
              <h4 className="font-semibold text-slate-800 mb-2">{camera.camera_name}</h4>
              <p className="text-xs text-slate-500">IP Link: {camera.ip_address}</p>
              <p className="text-xs text-slate-500">Zone Key: {camera.zone_name || 'Assigned'}</p>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={() => { setEditingId(camera.camera_id); setFormData({name: camera.camera_name, ip: camera.ip_address, zone_id: camera.zone_id}); setShowForm(true); }} className="flex-1 py-2 bg-slate-50 text-slate-600 rounded-lg flex justify-center items-center text-xs gap-1"><Edit2 size={12}/> Edit</button>
              <button onClick={() => handleDelete(camera.camera_id)} className="flex-1 py-2 bg-red-50 text-red-600 rounded-lg text-xs flex justify-center items-center gap-1"><Trash2 size={12}/> Remove</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Tab 4: Teacher Provisioning (Manager Administrative Bound Context)
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '', full_name: '', phone_number: '' });

  const fetchTeachers = () => {
    setLoading(true);
    axiosInstance.get('/manager/teachers') // Routes through designated management endpoints
      .then(res => {
        setUsers(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to extract active teacher directories:", err);
        setLoading(false);
      });
  };

  useEffect(() => { fetchTeachers(); }, []);

  const handleAddUser = () => {
    axiosInstance.post('/manager/provision-teacher', {
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
      phone_number: formData.phone_number
    })
    .then(() => {
      fetchTeachers();
      setShowForm(false);
      setFormData({ email: '', password: '', full_name: '', phone_number: '' });
    })
    .catch(err => alert(err.response?.data?.detail || "Provision failure"));
  };

  if (loading) return <div className="text-slate-400 font-mono text-xs py-4">SYNCING STAFF PROVISIONS...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2">
          <Plus size={20} /> Add Staff Teacher
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <input placeholder="Full Legal Name" value={formData.full_name} onChange={(e) => setFormData({...formData, full_name: e.target.value})} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <input placeholder="Staff Institution Email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <input placeholder="Mobile Contact Sequence" value={formData.phone_number} onChange={(e) => setFormData({...formData, phone_number: e.target.value})} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <input type="password" placeholder="Temporary System Password Key" value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <div className="flex gap-2">
            <button onClick={handleAddUser} className="px-4 py-2 bg-brand-500 text-white rounded-xl">Provision Access</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-slate-200 rounded-xl">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-700 text-sm font-semibold">
              <th className="p-4">Name</th>
              <th className="p-4">Email Address</th>
              <th className="p-4">Scope Scope Privilege</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.user_id} className="border-b border-slate-100 text-slate-700 hover:bg-slate-50/50">
                <td className="p-4 font-medium">{u.full_name}</td>
                <td className="p-4 text-slate-500">{u.email}</td>
                <td className="p-4"><span className="px-2.5 py-1 bg-indigo-50 text-indigo-600 font-bold rounded-lg text-xs">TEACHER</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Tab 5: Dynamic Performance Matrices Analytics
const PerformanceTab = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    axiosInstance.get('/manager/performance-dashboard')
      .then(res => setStats(res.data))
      .catch(err => console.error("Could not trace historic analytical graphs:", err));
  }, []);

  if (!stats) return <div className="text-slate-400 font-mono text-xs py-4">MAPPING ANALYTICAL MATRICES...</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Alert Distributions Mapped by Zone Areas</h3>
          <div className="space-y-4">
            {stats.zones_performance?.map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <p className="font-medium text-slate-700 text-sm">{item.zone_name}</p>
                  <p className="text-xs text-slate-500 font-bold">{item.total_incidents} logged security incidents</p>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div className="bg-indigo-600 h-2 rounded-full transition-all duration-500" style={{ width: `${Math.min((item.total_incidents / 20) * 100, 100)}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Mean Average Staff Latency Delay Profiles</h3>
            <div className="space-y-3">
              {stats.zones_performance?.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <p className="text-sm font-semibold text-slate-700">{item.zone_name}</p>
                  <p className="text-brand-500 font-black text-sm">{item.average_response_time_seconds ? `${Math.round(item.average_response_time_seconds)}s` : '0s delay'}</p>
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-400 font-mono uppercase mt-6 pt-4 border-t border-slate-100">Gross Nursery Mean Average Target Boundary: <span className="font-bold text-slate-700">{stats.summary?.nursery_average_response_time_seconds || 0}s</span></p>
        </div>
      </div>
    </div>
  );
};

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');
  
  // Extract account configurations securely from unified local memory
  const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
  const role = storedUser ? JSON.parse(storedUser)?.role?.toLowerCase() : 'manager';

  const isManager = role === 'manager';
  const isParent = role === 'parent';

  const showCameras = isManager || isParent;
  const showUsers = isManager;
  const showPerformance = isManager;

  const tabs = [
    { key: 'profile', label: 'Profile', show: true },
    { key: 'notifications', label: 'Notifications', show: true },
    { key: 'cameras', label: 'Cameras', show: showCameras },
    { key: 'users', label: 'Teacher Management', show: showUsers },
    { key: 'performance', label: 'Analytics', show: showPerformance },
  ];

  useEffect(() => {
    if (!tabs.find(t => t.key === activeTab && t.show)) {
      const firstAllowed = tabs.find(t => t.show);
      if (firstAllowed) setActiveTab(firstAllowed.key);
    }
  }, [role]);

  return (
    <div className="space-y-6 p-2">
      <header className="mb-6">
        <h2 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
          <User size={32} className="text-brand-500" />
          Settings Configuration Center
        </h2>
        <p className="text-slate-500 mt-1 text-sm">Manage system telemetry preferences, notification endpoints, and user hierarchies</p>
      </header>

      {/* Dynamic Tab Switchboards Navigation */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-3 flex flex-wrap gap-2">
        {tabs.filter(t => t.show).map(tab => (
          <TabButton key={tab.key} tab={tab.key} activeTab={activeTab} onClick={setActiveTab} label={tab.label} />
        ))}
      </div>

      {/* Tab Panel Viewports */}
      <div className="mt-4">
        {activeTab === 'profile' && <EditProfile />}
        {activeTab === 'notifications' && <NotificationsTab />}
        {activeTab === 'cameras' && showCameras && <ManageCameras role={role} />}
        {activeTab === 'users' && showUsers && <UserManagement />}
        {activeTab === 'performance' && showPerformance && <PerformanceTab />}
      </div>
    </div>
  );
}