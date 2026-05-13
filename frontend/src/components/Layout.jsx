import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Eye, AlertTriangle, FileText, Settings, Info, LogOut } from 'lucide-react';

const NavItem = ({ to, icon: Icon, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link 
      to={to} 
      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
        isActive 
          ? 'bg-brand-500 text-white font-medium shadow-md' 
          : 'text-slate-500 hover:bg-brand-100 hover:text-brand-500'
      }`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  );
};

export default function Layout({ children }) {
  let role = null;
  try {
    role = JSON.parse(sessionStorage.getItem('user'))?.role || null;
  } catch (e) {
    role = null;
  }

  const isTeacher = role === 'teacher';
  const navigate = useNavigate();

  const handleSignOut = () => {
    try { 
      sessionStorage.removeItem('user'); 
    } catch (e) {}
    navigate('/login', { replace: true });
  };

  return (
    <div className="flex h-screen bg-slate-50">
      <aside className="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col p-6 shadow-sm">
        <div className="mb-8 flex justify-center">
          <img src="/Yaqidh-logo.png" alt="Yaqidh Logo" className="h-16 w-auto object-contain mix-blend-multiply" />
        </div>
        
        <nav className="space-y-2 flex-1">
          {!isTeacher && <NavItem to="/" icon={LayoutDashboard} label="Dashboard" />}
          {!isTeacher && <NavItem to="/live" icon={Eye} label="Live Monitoring" />}
          <NavItem to="/incidents" icon={AlertTriangle} label="Incidents" />
          {!isTeacher && <NavItem to="/reports" icon={FileText} label="Reports" />}
          <NavItem to="/settings" icon={Settings} label="Settings" />
        </nav>
        
        <div className="mt-auto pt-4 border-t border-slate-100 space-y-2">
          <NavItem to="/about" icon={Info} label="About System" />
          <button
            onClick={handleSignOut}
            className="w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-slate-500 hover:bg-red-50 hover:text-red-600"
          >
            <LogOut size={20} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-4 md:p-8">
        {children}
      </main>
    </div>
  );
}