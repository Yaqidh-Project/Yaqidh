import React, { useState, useEffect } from 'react';
import { User, Bell, Camera, Users, Upload, Plus, Edit2, Trash2, RefreshCw, MapPin } from 'lucide-react';
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

// Tab 1: Edit Profile
const EditProfile = () => {
  const [profileData, setProfileData] = useState({ name: '', email: '', phone: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

// Tab 2: Notifications
const NotificationsTab = () => {
  const [notifications, setNotifications] = useState({
    email: true,
    app: true,
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
              <p className="text-sm text-slate-500">Receive safety alerts via email</p>
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
              <p className="font-medium text-slate-800">Mobile Push</p>
              <p className="text-sm text-slate-500">Receive real-time push notifications</p>
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

// Tab 3: Manage Zones (Manager + Parent)
const ManageZones = () => {
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ zone_name: '', description: '' });

  const fetchZones = () => {
    setLoading(true);
    axiosInstance.get('/zones')
      .then(res => {
        setZones(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load zones:", err);
        setLoading(false);
      });
  };

  useEffect(() => { fetchZones(); }, []);

  const resetForm = () => {
    setFormData({ zone_name: '', description: '' });
    setEditingId(null);
    setShowForm(false);
  };

  const handleSave = () => {
    if (!formData.zone_name.trim()) return alert("Zone name is required.");

    const request = editingId
      ? axiosInstance.patch(`/zones/${editingId}`, formData)
      : axiosInstance.post('/zones', formData);

    request
      .then(() => { fetchZones(); resetForm(); })
      .catch(err => console.error("Failed to save zone:", err));
  };

  const handleEdit = (zone) => {
    setEditingId(zone.zone_id);
    setFormData({ zone_name: zone.zone_name, description: zone.description || '' });
    setShowForm(true);
  };

  const handleDelete = (id) => {
    if (window.confirm("Delete this zone? Cameras assigned to it will be unassigned.")) {
      axiosInstance.delete(`/zones/${id}`)
        .then(() => fetchZones())
        .catch(err => console.error("Failed to delete zone:", err));
    }
  };

  if (loading) return <div className="text-slate-400 font-mono text-xs py-4">LOADING ZONES...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800">Monitored Zones</h3>
          <button
            onClick={() => { resetForm(); setShowForm(!showForm); }}
            className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2 text-sm"
          >
            <Plus size={18} /> Add Zone
          </button>
        </div>

        {showForm && (
          <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 space-y-4">
            <h4 className="font-semibold text-slate-700 text-sm">{editingId ? 'Edit Zone' : 'New Zone'}</h4>
            <input
              placeholder="Zone Name (e.g. Playground, Classroom A)"
              value={formData.zone_name}
              onChange={(e) => setFormData({ ...formData, zone_name: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
            />
            <input
              placeholder="Description (optional)"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
            />
            <div className="flex gap-2 justify-end text-sm">
              <button onClick={resetForm} className="px-4 py-2 bg-slate-200 text-slate-700 rounded-xl font-medium">
                Cancel
              </button>
              <button onClick={handleSave} className="px-4 py-2 bg-brand-500 text-white rounded-xl font-medium">
                {editingId ? 'Save Changes' : 'Add Zone'}
              </button>
            </div>
          </div>
        )}

        {zones.length === 0 ? (
          <div className="text-center py-12 text-slate-400 rounded-2xl border border-dashed border-slate-200">
            <MapPin size={36} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">No zones added yet. Add your first zone to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {zones.map(zone => (
              <div key={zone.zone_id} className="bg-slate-50/50 p-4 rounded-xl border border-slate-100 flex flex-col justify-between hover:border-slate-200 transition">
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-2 bg-brand-50 rounded-lg mt-0.5">
                    <MapPin size={16} className="text-brand-500" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-800 text-sm">{zone.zone_name}</h4>
                    {zone.description && (
                      <p className="text-xs text-slate-500 mt-0.5">{zone.description}</p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(zone)}
                    className="flex-1 py-2 bg-white text-slate-600 rounded-lg flex justify-center items-center text-xs gap-1 border border-slate-100 hover:bg-slate-50 transition"
                  >
                    <Edit2 size={12} /> Edit
                  </button>
                  <button
                    onClick={() => handleDelete(zone.zone_id)}
                    className="flex-1 py-2 bg-red-50 text-red-600 rounded-lg text-xs flex justify-center items-center gap-1 hover:bg-red-100 transition"
                  >
                    <Trash2 size={12} /> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Tab 4: Manage Cameras (Manager + Parent)
const ManageCameras = ({ role }) => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', ip: '', stream_url: '', zone_id: '', status: 'Online' });
  const [zones, setZones] = useState([]);

  const fetchCamerasAndZones = () => {
    setLoading(true);
    Promise.all([axiosInstance.get('/cameras'), axiosInstance.get('/zones')])
      .then(([camRes, zoneRes]) => {
        setCameras(camRes.data);
        setZones(zoneRes.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load cameras:", err);
        setLoading(false);
      });
  };

  useEffect(() => { fetchCamerasAndZones(); }, []);

  const handleAddCamera = () => {
    if (!formData.name.trim() || !formData.ip.trim() || !formData.stream_url.trim()) {
      return alert("Camera name, IP address, and Stream URL are required.");
    }

    let sanitizedZoneId = formData.zone_id === "" ? null : formData.zone_id;
    if (sanitizedZoneId && !isNaN(sanitizedZoneId)) {
      sanitizedZoneId = Number(sanitizedZoneId);
    }

    if (editingId) {
      axiosInstance.patch(`/cameras/${editingId}`, { 
        camera_name: formData.name, 
        ip_address: formData.ip,
        stream_url: formData.stream_url
      })
      .then(() => { 
        fetchCamerasAndZones(); 
        setShowForm(false); 
        setEditingId(null); 
        setFormData({ name: '', ip: '', stream_url: '', zone_id: '', status: 'Online' });
      })
      .catch(err => {
        console.error("Failed to patch camera structure:", err.response?.data?.detail || err.message);
        alert("Unable to save edits: " + JSON.stringify(err.response?.data?.detail || "Schema mismatch"));
      });
    } else {
      axiosInstance.post('/cameras', { 
        camera_name: formData.name, 
        ip_address: formData.ip, 
        stream_url: formData.stream_url,
        zone_id: sanitizedZoneId 
      })
      .then(() => { 
        fetchCamerasAndZones(); 
        setShowForm(false); 
        setFormData({ name: '', ip: '', stream_url: '', zone_id: '', status: 'Online' });
      })
      .catch(err => {
        console.error("FastAPI Validation Detail Payload:", err.response?.data?.detail || err.message);
        alert("Failed adding camera: " + JSON.stringify(err.response?.data?.detail || "Check entity parameters"));
      });
    }
  };

  const handleDelete = (id) => {
    if (window.confirm("Delete this camera?")) {
      axiosInstance.delete(`/cameras/${id}`).then(() => fetchCamerasAndZones());
    }
  };

  if (loading) return <div className="text-slate-400 font-mono text-xs py-4">LOADING CAMERAS...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800">Connected Cameras</h3>
          <button 
            onClick={() => {
              setEditingId(null);
              setFormData({ name: '', ip: '', stream_url: '', zone_id: '', status: 'Online' });
              setShowForm(!showForm);
            }} 
            className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2 text-sm"
          >
            <Plus size={18} /> Add Camera
          </button>
        </div>

        {showForm && (
          <div className="p-5 bg-slate-50 rounded-2xl border border-slate-100 space-y-4">
            <h4 className="font-semibold text-slate-700 text-sm">{editingId ? 'Edit Camera' : 'New Camera'}</h4>
            <input
              placeholder="Camera Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
            />
            <input
              placeholder="IP Address"
              value={formData.ip}
              onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
            />
            <input
              placeholder="Stream URL (e.g., rtsp://... or video source link)"
              value={formData.stream_url}
              onChange={(e) => setFormData({ ...formData, stream_url: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
            />
            <select
              value={formData.zone_id}
              onChange={(e) => setFormData({ ...formData, zone_id: e.target.value })}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm"
            >
              <option value="">Select Zone (Optional)</option>
              {zones.map(z => <option key={z.zone_id} value={z.zone_id}>{z.zone_name}</option>)}
            </select>
            <div className="flex gap-2 justify-end text-sm">
              <button 
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setFormData({ name: '', ip: '', stream_url: '', zone_id: '', status: 'Online' });
                }} 
                className="px-4 py-2 bg-slate-200 text-slate-700 rounded-xl font-medium"
              >
                Cancel
              </button>
              <button onClick={handleAddCamera} className="px-4 py-2 bg-brand-500 text-white rounded-xl font-medium hover:bg-brand-600 transition">
                {editingId ? 'Save' : 'Add'}
              </button>
            </div>
          </div>
        )}

        {cameras.length === 0 ? (
          <div className="text-center py-12 text-slate-400 rounded-2xl border border-dashed border-slate-200">
            <Camera size={36} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">No hardware feeds connected yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cameras.map(camera => (
              <div key={camera.camera_id} className="bg-slate-50/50 p-4 rounded-xl border border-slate-100 flex flex-col justify-between hover:border-slate-200 transition">
                <div>
                  <h4 className="font-semibold text-slate-800 text-sm mb-2">{camera.camera_name}</h4>
                  <p className="text-xs text-slate-500">IP: {camera.ip_address}</p>
                  {camera.stream_url && <p className="text-xs text-slate-400 truncate">URL: {camera.stream_url}</p>}
                  <p className="text-xs text-slate-500">Zone: {zones.find(z => String(z.zone_id) === String(camera.zone_id))?.zone_name || '—'}</p>
                </div>
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => { 
                      setEditingId(camera.camera_id); 
                      setFormData({ 
                        name: camera.camera_name, 
                        ip: camera.ip_address, 
                        stream_url: camera.stream_url || '', 
                        zone_id: camera.zone_id || '', 
                        status: 'Online' 
                      }); 
                      setShowForm(true); 
                    }}
                    className="flex-1 py-2 bg-white text-slate-600 rounded-lg flex justify-center items-center text-xs gap-1 border border-slate-100 hover:bg-slate-50 transition"
                  >
                    <Edit2 size={12} /> Edit
                  </button>
                  <button
                    onClick={() => handleDelete(camera.camera_id)}
                    className="flex-1 py-2 bg-red-50 text-red-600 rounded-lg text-xs flex justify-center items-center gap-1 hover:bg-red-100 transition"
                  >
                    <Trash2 size={12} /> Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Tab 5: Teacher Management (Manager only)
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '', full_name: '', phone_number: '' });

  const fetchTeachers = () => {
    setLoading(true);
    axiosInstance.get('/manager/teachers')
      .then(res => { setUsers(res.data); setLoading(false); })
      .catch(err => { console.error("Failed to load teachers:", err); setLoading(false); });
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
    .catch(err => alert(err.response?.data?.detail || "Failed to add teacher"));
  };

  if (loading) return <div className="text-slate-400 font-mono text-xs py-4">LOADING TEACHERS...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button onClick={() => setShowForm(!showForm)} className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2">
          <Plus size={20} /> Add Teacher
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <input placeholder="Full Name" value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <input placeholder="Email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <input placeholder="Phone Number" value={formData.phone_number} onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <input type="password" placeholder="Temporary Password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none" />
          <div className="flex gap-2">
            <button onClick={handleAddUser} className="px-4 py-2 bg-brand-500 text-white rounded-xl">Add</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-slate-200 rounded-xl">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-700 text-sm font-semibold">
              <th className="p-4">Name</th>
              <th className="p-4">Email</th>
              <th className="p-4">Role</th>
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

// Tab 6: Analytics (Manager only)
const PerformanceTab = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    axiosInstance.get('/manager/performance-dashboard')
      .then(res => setStats(res.data))
      .catch(err => console.error("Failed to load analytics:", err));
  }, []);

  if (!stats) return <div className="text-slate-400 font-mono text-xs py-4">LOADING ANALYTICS...</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Alerts by Zone</h3>
          <div className="space-y-4">
            {stats.zones_performance?.map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <p className="font-medium text-slate-700 text-sm">{item.zone_name}</p>
                  <p className="text-xs text-slate-500 font-bold">{item.total_incidents} incidents</p>
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
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Avg Response Time by Zone</h3>
            <div className="space-y-3">
              {stats.zones_performance?.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <p className="text-sm font-semibold text-slate-700">{item.zone_name}</p>
                  <p className="text-brand-500 font-black text-sm">{item.average_response_time_seconds ? `${Math.round(item.average_response_time_seconds)}s` : '0s'}</p>
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-400 font-mono uppercase mt-6 pt-4 border-t border-slate-100">
            Nursery Average: <span className="font-bold text-slate-700">{stats.summary?.nursery_average_response_time_seconds || 0}s</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');

  const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
  const role = storedUser ? JSON.parse(storedUser)?.role?.toLowerCase() : 'manager';

  const isManager = role === 'manager';
  const isParent = role === 'parent';

  const tabs = [
    { key: 'profile',      label: 'Profile',             show: true },
    { key: 'notifications',label: 'Notifications',        show: true },
    { key: 'zones',        label: 'Zones',                show: isManager || isParent },
    { key: 'cameras',      label: 'Cameras',              show: isManager || isParent },
    { key: 'users',        label: 'Teacher Management',   show: isManager },
    { key: 'performance',  label: 'Analytics',            show: isManager },
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
          Settings
        </h2>
        <p className="text-slate-500 mt-1 text-sm">Manage your profile, zones, cameras, and system preferences</p>
      </header>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-3 flex flex-wrap gap-2">
        {tabs.filter(t => t.show).map(tab => (
          <TabButton key={tab.key} tab={tab.key} activeTab={activeTab} onClick={setActiveTab} label={tab.label} />
        ))}
      </div>

      <div className="mt-4">
        {activeTab === 'profile'       && <EditProfile />}
        {activeTab === 'notifications' && <NotificationsTab />}
        {activeTab === 'zones'         && (isManager || isParent) && <ManageZones />}
        {activeTab === 'cameras'       && (isManager || isParent) && <ManageCameras role={role} />}
        {activeTab === 'users'         && isManager && <UserManagement />}
        {activeTab === 'performance'   && isManager && <PerformanceTab />}
      </div>
    </div>
  );
}