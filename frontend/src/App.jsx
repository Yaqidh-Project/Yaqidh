import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LiveMonitoring from './pages/LiveMonitoring'; // Ensure this points to your new functional file
import Incidents from './pages/Incidents';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
import About from './pages/About';
import ForgotPassword from './pages/ForgotPassword';

// Component to show error message on login if redirected
const LoginWithError = () => {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const error = params.get('error');

  return (
    <>
      {error === "invalid" && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-red-600 text-white px-6 py-2 rounded-full shadow-lg text-sm font-bold">
          Access Denied: You do not have permission for that section.
        </div>
      )}
      <Login />
    </>
  );
};

// RequireRole component - Controls access to specific pages
const RequireRole = ({ allowed = [], children }) => {
  let role = null;
  try {
    role = JSON.parse(sessionStorage.getItem('user'))?.role;
  } catch (e) {
    role = null;
  }

  if (allowed.length === 0) return children;
  if (role && allowed.includes(role)) return children;

  return <Navigate to="/login?error=invalid" replace />;
};

// Default redirect logic based on Aliyah's project requirements
const DefaultRedirect = () => {
  const userStr = sessionStorage.getItem('user');
  if (!userStr) return <Navigate to="/login" replace />;

  const role = JSON.parse(userStr)?.role;
  if (role === "manager" || role === "parent") return <Navigate to="/dashboard" replace />;
  if (role === "teacher") return <Navigate to="/incidents" replace />;

  return <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Auth Routes */}
        <Route path="/login" element={<LoginWithError />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* Root Redirect after login/register */}
        <Route path="/" element={<DefaultRedirect />} />

        {/* Protected System Routes wrapped in Layout */}
        <Route
          path="/*"
          element={
            <RequireRole allowed={["teacher", "manager", "parent"]}>
              <Layout>
                <Routes>
                  {/* Dashboard → Manager & Parent */}
                  <Route 
                    path="/dashboard" 
                    element={
                      <RequireRole allowed={["manager", "parent"]}>
                        <Dashboard />
                      </RequireRole>
                    } 
                  />

                  {/* Live AI Monitoring → Manager & Parent */}
                  <Route 
                    path="/live" 
                    element={
                      <RequireRole allowed={["manager", "parent"]}>
                        <LiveMonitoring />
                      </RequireRole>
                    } 
                  />

                  {/* Incidents Tracking */}
                  <Route 
                    path="/incidents" 
                    element={<Incidents />} 
                  />

                  {/* Analytical Reports */}
                  <Route 
                    path="/reports" 
                    element={
                      <RequireRole allowed={["manager", "parent"]}>
                        <Reports />
                      </RequireRole>
                    } 
                  />

                  {/* System Settings */}
                  <Route path="/settings" element={<Settings />} />

                  {/* About the System */}
                  <Route path="/about" element={<About />} />

                  {/* Fallback for within layout */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            </RequireRole>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;