import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      setError('Please enter a valid email address structure (e.g., name@example.com)');
      return;
    }

    setLoading(true);

    try {
      // Dispatch password recovery request directly to FastAPI auth router
      await axiosInstance.post('/auth/forgot-password', {
        email: email
      });

      setMessage(`If an active account exists for ${email}, a password reset link has been dispatched.`);
      setEmail('');

      // Route the user to /reset-password
      setTimeout(() => {
        navigate('/reset-password', { state: { email: email } });
      }, 3000);

    } catch (err) {
      console.error("Password recovery pipeline failure:", err);
      const backendDetail = err.response?.data?.detail;
      if (typeof backendDetail === 'string') {
        setError(backendDetail);
      } else {
        setError('An unexpected error occurred. Please verify your connection and try again.');
      }
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
          <h1 className="text-3xl font-bold text-slate-800 mt-4 tracking-tight">Forgot Password</h1>
          <p className="text-slate-500 mt-2 text-sm">Enter your registered email address below, and we will transmit a secure access reset link pipeline.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8 border border-slate-100">
          {message && (
            <div className="mb-4 p-4 bg-emerald-50 border border-emerald-100 rounded-xl text-emerald-700 text-sm font-semibold animate-pulse">
              {message}
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3.5 text-slate-400" size={20} />
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3.5 rounded-xl transition duration-200 disabled:opacity-50 flex items-center justify-center gap-2 shadow-md shadow-brand-500/10 active:scale-[0.98]"
            >
              {loading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Processing...
                </>
              ) : (
                'Send Reset Link'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link 
              to="/login" 
              className="inline-flex items-center gap-2 text-sm text-brand-500 hover:text-brand-600 font-semibold group transition-all"
            >
              <ArrowLeft size={16} className="transition-transform group-hover:-translate-x-1" />
              Remembered your password? Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}