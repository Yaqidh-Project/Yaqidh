import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const isRegisteredSuccess = queryParams.get('registered') === 'success';

  const normalizeRole = (roleRaw) => {
    if (!roleRaw) return '';
    if (Array.isArray(roleRaw)) {
      return roleRaw.map((x) => String(x).trim().toLowerCase());
    }
    return String(roleRaw).trim().toLowerCase();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.email || !formData.password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);

    try {
      const response = await axiosInstance.post('/auth/login', {
        email: formData.email,
        password: formData.password,
      });

      console.log('[LOGIN] Response received:', response.data);
      
      if (response.data && response.data.requires_verification === true) {
        console.log('[LOGIN] Phone verification required - redirecting to /verify-otp');
        localStorage.setItem('verify_email', formData.email);
        localStorage.setItem('verification_endpoint', response.data.verification_endpoint || '/auth/signup/verify-otp');
        navigate(`/verify-otp?email=${encodeURIComponent(formData.email)}`);
        return;
      }

      if (response.data && response.data.access_token) {
        console.log('[LOGIN] Token received - storing and redirecting to dashboard');
        
        localStorage.setItem('token', response.data.access_token);
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        
        const roleRaw = response.data.user?.role ?? response.data.user?.role_name ?? response.data.role;
        const cleanRole = normalizeRole(roleRaw);

        localStorage.setItem('user', JSON.stringify({
          email: response.data.user?.email || formData.email,
          role: cleanRole
        }));

        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        window.location.href = '/';
        return;
      }
      
      console.error('[LOGIN] Unexpected response - no token and no verification required');
      setError('Unexpected server response. Please try again.');
    } catch (err) {
      console.error(err);
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          setError(err.response.data.detail);
        } else if (Array.isArray(err.response.data.detail)) {
          setError(err.response.data.detail[0]?.msg || 'Validation error');
        } else {
          setError('Invalid server response');
        }
      } else {
        setError('Invalid email or password.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <img src="/Yaqidh-logo.png" alt="Yaqidh Logo" className="h-16 w-auto mx-auto mb-4 object-contain" />
          <h1 className="text-3xl font-black text-brand-500 tracking-tighter italic">WELCOME BACK</h1>
          <p className="text-slate-400 font-bold uppercase text-[10px] tracking-widest mt-1">Sign in to your account</p>
        </div>

        {isRegisteredSuccess && (
          <div className="mb-2 p-4 bg-emerald-600 rounded-2xl text-white text-xs font-black text-center shadow-xl shadow-emerald-600/20 raw-uppercase tracking-wide">
            ACCOUNT ACTIVATED SUCCESSFULLY! PLEASE LOG IN WITH YOUR CREDENTIALS.
          </div>
        )}

        <div className="bg-white p-10 rounded-[3rem] shadow-2xl border border-slate-100">
          {error && (
            <div className="mb-6 p-4 bg-red-600 rounded-2xl text-white text-xs font-black text-center">
              {error.toUpperCase()}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div className="relative">
              <Mail className="absolute left-4 top-4 text-slate-300" size={18} />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Email Address"
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none font-medium"
                required
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-4 top-4 text-slate-300" size={18} />
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Password"
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none font-medium"
                required
              />
            </div>

            <div className="flex justify-end pt-1">
              <Link 
                to="/forgot-password" 
                className="text-xs font-bold uppercase tracking-wider text-slate-400 hover:text-brand-500 transition-colors duration-200"
              >
                Forgot Password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-500 hover:bg-brand-600 text-white font-black py-5 rounded-2xl shadow-xl shadow-brand-500/30 flex items-center justify-center gap-2 mt-6 transition-transform active:scale-95 disabled:opacity-50"
            >
              {loading ? 'AUTHENTICATING...' : 'SIGN IN'} <ArrowRight size={20} />
            </button>
          </form>

          <div className="mt-8 text-center pt-6 border-t border-slate-50">
            <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">
              Don't have an account?{' '}
              <Link to="/register" className="text-brand-500 hover:underline">
                Register Here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}