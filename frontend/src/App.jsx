import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LiveMonitoring from './pages/LiveMonitoring'; 
import Incidents from './pages/Incidents';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
import About from './pages/About';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword'; // Imported the password modification interface framework

// Component to show access denied error message on login if redirected from a guard block
const LoginWithError = () => {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const error = params.get('error');

  return (
    <>
      {error === "invalid" && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-red-600 text-white px-6 py-2 rounded-full shadow-lg text-sm font-bold animate-bounce">
          Access Denied: You do not have permission for that section.
        </div>
      )}
      <Login />
    </>
  );
};

// RequireRole component - Secure route guard checking for dynamic authorized system privileges
const RequireRole = ({ allowed = [], children }) => {
  let role = null;
  try {
    // Flexibly falls back to check both storage scopes to eliminate authorization drops
    const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
    role = storedUser ? JSON.parse(storedUser)?.role : null;
  } catch (e) {
    console.error("Failed to extract account authorization properties:", e);
    role = null;
  }

  if (allowed.length === 0) return children;
  if (role && allowed.includes(role.toLowerCase())) return children;

  return <Navigate to="/login?error=invalid" replace />;
};

// Default redirect engine determining navigation landing targets upon authentication states
const DefaultRedirect = () => {
  const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
  if (!userStr) return <Navigate to="/login" replace />;

  try {
    const role = JSON.parse(userStr)?.role;
    if (role === "manager" || role === "parent") return <Navigate to="/dashboard" replace />;
    if (role === "teacher") return <Navigate to="/incidents" replace />;
  } catch (e) {
    console.error("Malformed storage user payload context execution:", e);
  }

  return <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Authentication Pipelines */}
        <Route path="/login" element={<LoginWithError />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        
        {/* Unsecured Public Password Reset Pipeline Target Component */}
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Global Hub Router Switchboard */}
        <Route path="/" element={<DefaultRedirect />} />

        {/* Secured System Topologies Covered by Master Layout Wrappers */}
        <Route
          path="/*"
          element={
            <RequireRole allowed={["teacher", "manager", "parent"]}>
              <Layout>
                <Routes>
                  {/* Dashboard Route -> Accessible by Manager and Parent scopes */}
                  <Route 
                    path="/dashboard" 
                    element={
                      <RequireRole allowed={["manager", "parent"]}>
                        <Dashboard />
                      </RequireRole>
                    } 
                  />

                  {/* Real-time Computer Vision Screen Frame Matrix */}
                  <Route 
                    path="/live" 
                    element={
                      <RequireRole allowed={["manager", "parent"]}>
                        <LiveMonitoring />
                      </RequireRole>
                    } 
                  />

                  {/* System Historic Alerts Log Context */}
                  <Route 
                    path="/incidents" 
                    element={
                      <RequireRole allowed={["manager", "parent", "teacher"]}>
                        <Incidents />
                      </RequireRole>
                    } 
                  />

                  {/* Deep Analytics Report Charts View */}
                  <Route 
                    path="/reports" 
                    element={
                      <RequireRole allowed={["manager", "parent"]}>
                        <Reports />
                      </RequireRole>
                    } 
                  />

                  {/* Functional Account & Settings Configuration Node */}
                  <Route path="/settings" element={<Settings />} />

                  {/* About the Yaqidh Framework Overview Documentation */}
                  <Route path="/about" element={<About />} />

                  {/* Structural Path Fallback Interface Re-routing */}
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