import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Lock, Eye, EyeOff, RefreshCw, ArrowLeft } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function ResetPassword() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract email dynamically passed from the previous ForgotPassword state navigation layer
  const [email, setEmail] = useState(location.state?.email || '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleReset = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!email) {
      setError('Email validation missing. Please restart the verification process.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      // Dispatch password modification payload directly to FastAPI auth router
      await axiosInstance.post('/auth/reset-password', {
        email: email,
        new_password: newPassword
      });

      setMessage('Password updated successfully! Redirecting to login page...');
      
      // Navigate cleanly back to login page after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      console.error("Reset pipeline exception structural trace:", err);
      setError(err.response?.data?.detail || 'Failed to update password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 flex flex-col items-center">
          <div className="bg-transparent p-2 transition-transform duration-300 hover:scale-105">
            <img 
              src="/Yaqidh-logo.png" 
              alt="Yaqidh Logo" 
              className="h-28 w-auto object-contain mix-blend-multiply" 
              style={{ filter: "contrast(1.1)" }}
            />
          </div>
          <h1 className="text-3xl font-bold text-slate-800 mt-4 tracking-tight">Create New Password</h1>
          <p className="text-slate-500 mt-2 text-sm">Please establish a strong security password configuration for account: <span className="font-semibold text-slate-700">{email}</span></p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8 border border-slate-100">
          {message && <div className="mb-4 p-4 bg-emerald-50 border border-emerald-100 rounded-xl text-emerald-700 text-sm font-semibold transition-all">{message}</div>}
          {error && <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold transition-all">{error}</div>}

          <form onSubmit={handleReset} className="space-y-5">
            {!location.state?.email && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Confirm Account Email</label>
                <input 
                  type="email" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)} 
                  className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500" 
                  required 
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 text-slate-400" size={20} />
                <input 
                  type={showPassword ? 'text' : 'password'} 
                  value={newPassword} 
                  onChange={(e) => setNewPassword(e.target.value)} 
                  placeholder="Minimum 6 characters" 
                  className="w-full pl-10 pr-10 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500" 
                  required 
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-3.5 text-slate-400">
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Confirm New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 text-slate-400" size={20} />
                <input 
                  type={showPassword ? 'text' : 'password'} 
                  value={confirmPassword} 
                  onChange={(e) => setConfirmPassword(e.target.value)} 
                  placeholder="Repeat new password" 
                  className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500" 
                  required 
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading} 
              className="w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3.5 rounded-xl transition duration-200 flex items-center justify-center gap-2 shadow-md shadow-brand-500/10 active:scale-[0.98]"
            >
              {loading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" /> 
                  Committing Changes...
                </>
              ) : (
                'Update Password'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/login" className="inline-flex items-center gap-2 text-sm text-brand-500 font-semibold group transition-all">
              <ArrowLeft size={16} className="transition-transform group-hover:-translate-x-1" /> 
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}