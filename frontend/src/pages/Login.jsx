import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
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
      const response = await axiosInstance.post('/auth/login', {
        email: email,
        password: password
      });

      if (response.data && response.data.access_token) {
        console.log("Login response:", response.data); 
        localStorage.setItem('token', response.data.access_token);
        
        const userPayload = JSON.stringify({ 
          email, 
          role: response.data.role.toLowerCase()
        });
        localStorage.setItem('user', userPayload);
        sessionStorage.setItem('user', userPayload);
        sessionStorage.setItem('token', response.data.access_token);
        
        navigate('/', { replace: true });
      }
    } catch (err) {
      console.error("Login authorization error metrics:", err);
      
      const status = err.response?.status;
      const backendDetail = err.response?.data?.detail;
      
      if (status === 404 || (typeof backendDetail === 'string' && backendDetail.toLowerCase().includes('not found'))) {
        setError("Account does not exist. Please register first.");
      } else if (status === 401 || (typeof backendDetail === 'string' && backendDetail.toLowerCase().includes('invalid'))) {
        setError("Invalid email or password. Please try again.");
      } else if (backendDetail) {
        if (typeof backendDetail === 'string') {
          setError(backendDetail);
        } else if (Array.isArray(backendDetail)) {
          setError(backendDetail[0]?.msg || 'Invalid data structure submitted.');
        } else {
          setError(JSON.stringify(backendDetail));
        }
      } else {
        setError('Failed to connect to the server. Please check your connection.');
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
               style={{ filter: "contrast(1.1)" }}
             />
          </div>
          <p className="text-slate-600 mt-3 font-medium tracking-wide">Security & Monitoring System</p>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8 border border-slate-100">
          <h2 className="text-2xl font-bold text-slate-800 mb-6 text-center">Welcome Back</h2>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold transition-all">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Email Address
              </label>
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

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 text-slate-400" size={20} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-10 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
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
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-600 text-sm">
              Don't have an account?{' '}
              <Link to="/register" className="text-brand-500 hover:text-brand-600 font-semibold">
                Register here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}