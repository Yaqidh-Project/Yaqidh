import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, Phone } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const [step, setStep] = useState(1); 
  const [phone, setPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('registered') === 'success') {
      setSuccessMessage('Verification completed successfully! Please sign in.');
    }
  }, [location]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.includes('@') || !emailRegex.test(email)) {
      setError('Please enter a valid email address structure (e.g., name@example.com)');
      return;
    }
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const res = await axiosInstance.post('/auth/login', { email, password });
      
      const { access_token, phone_number, user } = res.data || {};
      
      const extractedPhone = phone_number || user?.phone_number || res.data?.phone || '';
      setPhone(extractedPhone);

      if (access_token) {
        localStorage.setItem('token', access_token);
        sessionStorage.setItem('token', access_token);
        
        const basicUser = { email, role: String(res.data?.role || '').toLowerCase() };
        localStorage.setItem('user', JSON.stringify(basicUser));
        sessionStorage.setItem('user', JSON.stringify(basicUser));
        
        navigate('/', { replace: true });
        return;
      }

      setStep(2);
    } catch (err) {
      console.error(err);
      
      if (err?.response?.status === 200 || err?.status === 200) {
        const { access_token, phone_number, user } = err?.response?.data || {};
        const extractedPhone = phone_number || user?.phone_number || err?.response?.data?.phone || '';
        setPhone(extractedPhone);
        
        if (access_token) {
          localStorage.setItem('token', access_token);
          sessionStorage.setItem('token', access_token);
        }
        
        setStep(2);
        return;
      }

      const status = err?.response?.status;
      const backendDetail = err?.response?.data?.detail;

      if (status === 404 || (typeof backendDetail === 'string' && backendDetail.toLowerCase().includes('not found'))) {
        setError('Account does not exist. Please register first.');
      } else if (status === 401 || (typeof backendDetail === 'string' && backendDetail.toLowerCase().includes('invalid'))) {
        setError('Invalid email or password. Please try again.');
      } else if (backendDetail) {
        if (typeof backendDetail === 'string') setError(backendDetail);
        else if (Array.isArray(backendDetail)) setError(backendDetail[0]?.msg || 'Invalid data structure submitted.');
        else setError(JSON.stringify(backendDetail));
      } else {
        setError('Failed to connect to the server. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyPhone = async (e) => {
    e.preventDefault();
    setError('');

    if (!verificationCode) {
      setError('Please enter the 6-digit verification code');
      return;
    }
    setLoading(true);

    const codeClean = String(verificationCode).trim();
    
    // Fallback to "050" if the backend sent it as the user's phone identifier
    const currentPhone = phone || '050';

    try {
      // 1. Try registration style verification (Works for Parents/Managers)
      const response = await axiosInstance.post(`/auth/signup/verify-otp?phone_number=${currentPhone}&code=${codeClean}`);
      
      if (response.data?.access_token) {
        localStorage.setItem('token', response.data.access_token);
        sessionStorage.setItem('token', response.data.access_token);
      }
      
      navigate('/login?registered=success');
      window.location.reload(); 
    } catch (err) {
      console.warn("Signup OTP endpoint failed, trying login verification flow...", err);
      
      try {
        // 2. Try Teacher verification flow. 
        // If it requires standard auth headers, we provide temporary basic auth fallback or use the stored token if available.
        const response = await axiosInstance.post(`/auth/phone/verify-code?code=${codeClean}`, {}, {
          headers: {
            // In case the backend strictly requires email identity to bind verification session
            'X-User-Email': email 
          }
        });
        
        if (response.data?.access_token) {
          localStorage.setItem('token', response.data.access_token);
          sessionStorage.setItem('token', response.data.access_token);
        }
        
        navigate('/login?registered=success');
        window.location.reload();
      } catch (fallbackErr) {
        console.error("Both verification endpoints failed:", fallbackErr);
        setError(fallbackErr.response?.data?.detail || 'Invalid or expired code.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-10 flex flex-col items-center">
          <div className="bg-transparent p-2 transition-transform duration-300 hover:scale-105">
            <img
              src="/Yaqidh-logo.png"
              alt="Yaqidh Logo"
              className="h-28 w-auto object-contain mix-blend-multiply"
              style={{ filter: 'contrast(1.1)' }}
            />
          </div>
          <p className="text-slate-600 mt-3 font-medium tracking-wide">Security & Monitoring System</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8 border border-slate-100">
          <h2 className="text-2xl font-bold text-slate-800 mb-6 text-center">
            {step === 1 ? 'Welcome Back' : 'Verify Phone'}
          </h2>

          {successMessage && (
            <div className="mb-4 p-4 bg-green-50 border border-green-100 rounded-xl text-green-600 text-sm font-semibold transition-all text-center">
              {successMessage}
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold transition-all text-center">
              {error}
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3.5 text-slate-400" size={20} />
                  <input
                    type="text"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 transition text-slate-800 placeholder-slate-400"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3.5 text-slate-400" size={20} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full pl-10 pr-10 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 transition text-slate-800 placeholder-slate-400"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3.5 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <div className="text-right">
                <Link to="/forgot-password" className="text-sm text-brand-500 hover:text-brand-600 font-medium">
                  Forgot Password?
                </Link>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3.5 rounded-xl transition duration-200 disabled:opacity-50 shadow-md shadow-brand-500/20 active:scale-[0.98]"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>

              <div className="mt-6 text-center">
                <p className="text-slate-600 text-sm">
                  Don&apos;t have an account?{' '}
                  <Link to="/register" className="text-brand-500 hover:text-brand-600 font-semibold">
                    Register here
                  </Link>
                </p>
              </div>
            </form>
          ) : (
            <form onSubmit={handleVerifyPhone} className="space-y-6">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-50 text-brand-500 rounded-full mb-2">
                  <Phone size={32} />
                </div>
                <p className="text-xs text-slate-500 px-4">
                  Enter the 6-digit verification code sent to <span className="font-bold text-brand-500">{email}</span>
                </p>
              </div>

              <input
                type="text"
                maxLength="6"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                placeholder="000000"
                className="w-full text-center text-2xl tracking-[0.5em] font-black py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none"
                required
              />

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand-500 hover:bg-brand-600 text-white font-black py-5 rounded-2xl shadow-xl shadow-brand-500/30 transition-transform active:scale-95 disabled:opacity-50"
              >
                {loading ? 'VERIFYING...' : 'COMPLETE REGISTRATION'}
              </button>

              <button
                type="button"
                onClick={() => setStep(1)}
                className="w-full text-brand-500 font-black text-xs uppercase hover:underline text-center"
              >
                Back to Details
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}