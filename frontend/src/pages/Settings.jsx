import React, { useState, useEffect } from 'react';
import { User, Bell, Camera, Users, BarChart3, Upload, Plus, Edit2, Trash2 } from 'lucide-react';

const TabButton = ({ tab, activeTab, onClick, label }) => (
  <button
    onClick={() => onClick(tab)}
    className={`px-4 py-3 rounded-xl font-medium transition duration-200 ${
      activeTab === tab
        ? 'bg-brand-500 text-white'
        : 'text-slate-600 hover:bg-slate-100'
    }`}
  >
    {label}
  </button>
);

// Tab 1: Edit Profile
const EditProfile = () => {
  const [profileData, setProfileData] = useState({
    name: 'Sara Ahmed',
    email: 'sara.ahmed@example.com',
    phone: '+966 00 000 0000',
  });
  const [picture, setPicture] = useState(null);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };

  const handlePictureUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setPicture(file.name);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-semibold text-slate-800 mb-6">Profile Information</h3>

        {/* Profile Picture */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-3">Profile Picture</label>
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-brand-100 rounded-xl flex items-center justify-center">
              <User className="text-brand-500" size={32} />
            </div>
            <div>
              <label className="inline-block px-4 py-2 bg-brand-500 text-white rounded-xl cursor-pointer hover:bg-brand-600 transition font-medium text-sm">
                <Upload size={16} className="inline mr-2" />
                Upload Picture
                <input type="file" accept="image/*" onChange={handlePictureUpload} hidden />
              </label>
              {picture && <p className="text-sm text-slate-600 mt-2">{picture}</p>}
            </div>
          </div>
        </div>

        {/* Form Fields */}
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
              onChange={handleProfileChange}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
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

        <button className="mt-6 w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3 rounded-xl transition">
          Save Changes
        </button>
      </div>
    </div>
  );
};

// Tab 2: Notifications
const NotificationsTab = () => {
  const [notifications, setNotifications] = useState({
    sms: true,
    email: true,
    app: false,
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
              <p className="font-medium text-slate-800">SMS Notifications</p>
              <p className="text-sm text-slate-500">Receive alerts via SMS</p>
            </div>
            <button
              onClick={() => toggleNotification('sms')}
              className={`px-4 py-2 rounded-xl font-medium text-sm transition ${
                notifications.sms
                  ? 'bg-safe text-white'
                  : 'bg-slate-200 text-slate-600'
              }`}
            >
              {notifications.sms ? 'On' : 'Off'}
            </button>
          </div>

          <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition">
            <div>
              <p className="font-medium text-slate-800">Email Notifications</p>
              <p className="text-sm text-slate-500">Receive alerts via email</p>
            </div>
            <button
              onClick={() => toggleNotification('email')}
              className={`px-4 py-2 rounded-xl font-medium text-sm transition ${
                notifications.email
                  ? 'bg-safe text-white'
                  : 'bg-slate-200 text-slate-600'
              }`}
            >
              {notifications.email ? 'On' : 'Off'}
            </button>
          </div>

          <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition">
            <div>
              <p className="font-medium text-slate-800">Mobile App Notifications</p>
              <p className="text-sm text-slate-500">Receive push notifications</p>
            </div>
            <button
              onClick={() => toggleNotification('app')}
              className={`px-4 py-2 rounded-xl font-medium text-sm transition ${
                notifications.app
                  ? 'bg-safe text-white'
                  : 'bg-slate-200 text-slate-600'
              }`}
            >
              {notifications.app ? 'On' : 'Off'}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h3 className="text-lg font-semibold text-slate-800 mb-6">Dashboard Display</h3>

        <div className="flex items-center justify-between p-4 border border-slate-200 rounded-xl hover:bg-slate-50 transition">
          <div>
            <p className="font-medium text-slate-800">Color Indicators</p>
            <p className="text-sm text-slate-500">Show status colors on dashboard</p>
          </div>
          <button
            onClick={() => toggleNotification('dashboardIndicators')}
            className={`px-4 py-2 rounded-xl font-medium text-sm transition ${
              notifications.dashboardIndicators
                ? 'bg-safe text-white'
                : 'bg-slate-200 text-slate-600'
            }`}
          >
            {notifications.dashboardIndicators ? 'On' : 'Off'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Tab 3: Manage Cameras (Conditional Data)
const ManageCameras = ({ role }) => {
  // Define camera sets
  const managerCameras = [
    { id: 1, name: 'Outdoor Playground Cam', ip: '192.168.1.11', zone: 'Outdoor Playground', status: 'Online' },
    { id: 2, name: 'Classroom A cam', ip: '192.168.1.12', zone: 'Classroom A', status: 'Offline' },
    { id: 3, name: 'Classroom B cam', ip: '192.168.1.13', zone: 'Classroom B', status: 'Online' },
    { id: 4, name: 'Classroom C cam', ip: '192.168.1.14', zone: 'Classroom C', status: 'Online' },
  ];

  const parentCameras = [
    { id: 1, name: 'Living Room', ip: '192.168.0.5', zone: 'Living Area', status: 'Online' },
    { id: 2, name: 'Baby\'s Bedroom', ip: '192.168.0.6', zone: 'Bedroom', status: 'Online' },
    { id: 3, name: 'Garden / Backyard', ip: '192.168.0.7', zone: 'Garden', status: 'Offline' },
  ];

  const [cameras, setCameras] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({ name: '', ip: '', zone: '', status: 'Online' });

  // Initialize cameras based on role
  useEffect(() => {
    if (role === 'manager') {
      setCameras(managerCameras);
    } else {
      setCameras(parentCameras);
    }
  }, [role]);

  const handleAddCamera = () => {
    if (formData.name && formData.ip && formData.zone) {
      if (editingId) {
        setCameras(cameras.map(c => c.id === editingId ? { ...c, ...formData } : c));
        setEditingId(null);
      } else {
        setCameras([...cameras, { id: Date.now(), ...formData }]);
      }
      setFormData({ name: '', ip: '', zone: '', status: 'Online' });
      setShowForm(false);
    }
  };

  const handleEdit = (camera) => {
    setFormData(camera);
    setEditingId(camera.id);
    setShowForm(true);
  };

  const handleDelete = (id) => {
    setCameras(cameras.filter(c => c.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-slate-800">
          {role === 'manager' ? 'Nursery Camera System' : 'Home Monitoring System'}
        </h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2"
        >
          <Plus size={20} /> Add Camera
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h4 className="font-semibold text-slate-800 mb-4">{editingId ? 'Edit Camera' : 'Add New Camera'}</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              placeholder="Camera Name"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <input
              placeholder="IP Address"
              value={formData.ip}
              onChange={(e) => setFormData({...formData, ip: e.target.value})}
              className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <input
              placeholder="Zone (e.g., Bedroom, Play Area)"
              value={formData.zone}
              onChange={(e) => setFormData({...formData, zone: e.target.value})}
              className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <select
              value={formData.status}
              onChange={(e) => setFormData({...formData, status: e.target.value})}
              className="px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="Online">Online</option>
              <option value="Offline">Offline</option>
            </select>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleAddCamera}
              className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition"
            >
              {editingId ? 'Update' : 'Add'}
            </button>
            <button
              onClick={() => {setShowForm(false); setEditingId(null); setFormData({ name: '', ip: '', zone: '', status: 'Online' });}}
              className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-xl font-medium transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cameras.map(camera => (
          <div key={camera.id} className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100">
            <div className="flex items-start justify-between mb-3">
              <h4 className="font-semibold text-slate-800">{camera.name}</h4>
              <div className="flex flex-col items-center">
                <span
                  className={`px-4 py-2 rounded-full text-sm font-medium ${camera.status === 'Online' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
                >
                  {camera.status === 'Online' ? 'Active' : 'Offline'}
                </span>
              </div>
            </div>
            <p className="text-sm text-slate-600 mb-1">IP: {camera.ip}</p>
            <p className="text-sm text-slate-600 mb-3">Zone: {camera.zone}</p>
            <div className="flex gap-2">
              <button
                onClick={() => handleEdit(camera)}
                className="flex-1 px-2 py-2 bg-brand-100 hover:bg-brand-200 text-brand-600 rounded-lg font-medium text-sm transition flex items-center justify-center gap-1"
              >
                <Edit2 size={16} /> Edit
              </button>
              <button
                onClick={() => handleDelete(camera.id)}
                className="flex-1 px-4 py-2 bg-danger text-white rounded-lg font-medium text-sm transition hover:bg-danger-dark"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Tab 4: User Management (Manager Only)
const UserManagement = () => {
  const [users, setUsers] = useState([
    { id: 1, email: 'teacher1@nursery.com', zone: 'Nap Room', role: 'Teacher' },
    { id: 2, email: 'teacher2@nursery.com', zone: 'Play Area', role: 'Teacher' },
  ]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ email: '', zone: '', role: 'Teacher' });

  const handleAddUser = () => {
    if (formData.email && formData.zone) {
      setUsers([...users, { id: Date.now(), ...formData }]);
      setFormData({ email: '', zone: '', role: 'Teacher' });
      setShowForm(false);
    }
  };

  const handleRemoveUser = (id) => {
    setUsers(users.filter(u => u.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition flex items-center gap-2"
        >
          <Plus size={20} /> Add Teacher
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h4 className="font-semibold text-slate-800 mb-4">Add New Teacher</h4>
          <div className="space-y-4">
            <input
              placeholder="Email Address"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <input
              type="password"
              placeholder="Temporary Password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            <input
              placeholder="Assigned Zone"
              value={formData.zone}
              onChange={(e) => setFormData({...formData, zone: e.target.value})}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
            
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleAddUser}
              className="px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl font-medium transition"
            >
              Add Teacher
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-xl font-medium transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left px-6 py-3 font-semibold text-slate-700">Email</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-700">Zone</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-700">Role</th>
              <th className="text-left px-6 py-3 font-semibold text-slate-700">Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="border-b border-slate-100 hover:bg-slate-50 transition">
                <td className="px-6 py-4 text-slate-700">{user.email}</td>
                <td className="px-6 py-4 text-slate-700">{user.zone}</td>
                <td className="px-6 py-4">
                  <span className="px-3 py-1 bg-brand-100 text-brand-600 rounded-full text-sm font-medium">
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => handleRemoveUser(user.id)}
                    className="text-danger hover:text-danger hover:underline font-medium text-sm"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Tab 5: Performance & Routing
const PerformanceTab = () => {
  const zoneData = [
    { zone: 'Play Area', alerts: 12, avgResponse: '1.2m' },
    { zone: 'Nap Room', alerts: 8, avgResponse: '0.8m' },
    { zone: 'Cafeteria', alerts: 3, avgResponse: '1.5m' },
    { zone: 'Classrooms', alerts: 5, avgResponse: '2.3m' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Alert Distribution by Zone</h3>
          <div className="space-y-3">
            {zoneData.map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <p className="font-medium text-slate-700">{item.zone}</p>
                  <p className="text-sm text-slate-600">{item.alerts} alerts</p>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div
                    className="bg-brand-500 h-2 rounded-full"
                    style={{ width: `${(item.alerts / 12) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Average Response Time</h3>
          <div className="space-y-3">
            {zoneData.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                <p className="font-medium text-slate-700">{item.zone}</p>
                <p className="text-brand-600 font-semibold">{item.avgResponse}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-slate-600 mt-4">Overall Average: <span className="font-semibold text-slate-800">1.45 minutes</span></p>
        </div>
      </div>
    </div>
  );
};

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');
  // Get user role from sessionStorage
  let role = 'manager';
  try {
    const user = JSON.parse(sessionStorage.getItem('user'));
    if (user && user.role) role = user.role;
  } catch {}
  const isManager = role === 'manager';
  const isParent = role === 'parent';
  const isTeacher = role === 'teacher';

  // Tab visibility logic
  const showCameras = isManager || isParent;
  const showUsers = isManager;
  const showPerformance = isManager;

  // Tabs config
  const tabs = [
    { key: 'profile', label: 'Profile', show: true },
    { key: 'notifications', label: 'Notifications', show: true },
    { key: 'cameras', label: 'Cameras', show: showCameras },
    { key: 'users', label: 'Teacher Management', show: showUsers },
    { key: 'performance', label: 'Analytics', show: showPerformance },
  ];

  // If current tab is not allowed, switch to first allowed
  React.useEffect(() => {
    if (!tabs.find(t => t.key === activeTab && t.show)) {
      const first = tabs.find(t => t.show);
      if (first) setActiveTab(first.key);
    }
  }, [role]);

  return (
    <div className="space-y-6">
      <header className="mb-6">
        <h2 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
          <User size={32} className="text-brand-500" />
          Settings
        </h2>
        <p className="text-slate-500 mt-2">Manage your account and preferences</p>
      </header>

      {/* Tabs Navigation */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 flex flex-wrap gap-2">
        {tabs.filter(t => t.show).map(tab => (
          <TabButton key={tab.key} tab={tab.key} activeTab={activeTab} onClick={setActiveTab} label={tab.label} />
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'profile' && <EditProfile />}
        {activeTab === 'notifications' && <NotificationsTab />}
        {activeTab === 'cameras' && showCameras && <ManageCameras role={role} />}
        {activeTab === 'users' && showUsers && <UserManagement />}
        {activeTab === 'performance' && showPerformance && <PerformanceTab />}
      </div>
    </div>
  );
}