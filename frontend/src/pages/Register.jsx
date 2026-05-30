import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Phone, Lock, ArrowRight, ShieldCheck } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function Register() {
  const [step, setStep] = useState(1); // Step 1: Details, Step 2: SMS OTP Verification
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    role: 'Parent', // Must match the backend Enum casing (Parent or Manager)
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const validateForm = () => {
    if (!formData.fullName || !formData.email || !formData.phone || !formData.password || !formData.confirmPassword) {
      setError('Please fill in all required fields');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return false;
    }
    return true;
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) return;
    setLoading(true);

    try {
      const response = await axiosInstance.post('/auth/register', {
        full_name: formData.fullName,
        email: formData.email,
        password: formData.password,
        phone_number: formData.phone,
        role_name: formData.role, 
        notification_prefs: { sms: true, email: true, app: true }
      });

      localStorage.setItem('token', response.data.access_token);
      
      await axiosInstance.post(`/auth/signup/request-otp?phone_number=${encodeURIComponent(formData.phone)}`);
      console.log('✅ OTP sent successfully to email!');
      
      setStep(2);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
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

    try {
      await axiosInstance.post(`/auth/signup/verify-otp?phone_number=${encodeURIComponent(formData.phone)}&code=${verificationCode}`);
      
      localStorage.setItem('user', JSON.stringify({ email: formData.email, role: formData.role.toLowerCase() }));
      window.location.href = '/';
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Invalid or expired code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <img src="/Yaqidh-logo.png" alt="Yaqidh Logo" className="h-16 w-auto mx-auto mb-4 object-contain" />
          <h1 className="text-3xl font-black text-brand-500 tracking-tighter italic">CREATE ACCOUNT</h1>
          <p className="text-slate-400 font-bold uppercase text-[10px] tracking-widest mt-1">Step {step} of 2</p>
        </div>

        <div className="bg-white p-10 rounded-[3rem] shadow-2xl border border-slate-100">
          {error && (
            <div className="mb-6 p-4 bg-red-600 rounded-2xl text-white text-xs font-black text-center">
              {error.toUpperCase()}
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleRegister} className="space-y-5">
              <div className="relative">
                <User className="absolute left-4 top-4 text-slate-300" size={18} />
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  placeholder="Full Name"
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none font-medium"
                />
              </div>

              <div className="relative">
                <Mail className="absolute left-4 top-4 text-slate-300" size={18} />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="Email Address"
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none font-medium"
                />
              </div>

              <div className="relative">
                <Phone className="absolute left-4 top-4 text-slate-300" size={18} />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  placeholder="Phone Number (e.g. +966500000000)"
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none font-medium"
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
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-4 top-4 text-slate-300" size={18} />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="Confirm Password"
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none font-medium"
                />
              </div>

              <div className="pt-4 space-y-3">
                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest text-center">Account Type</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setFormData({...formData, role: 'Parent'})}
                    className={`py-4 rounded-2xl font-black text-xs transition-all border-2 ${
                      formData.role === 'Parent' 
                      ? 'border-brand-500 bg-brand-50 text-brand-500 shadow-inner' 
                      : 'border-slate-100 text-slate-400'
                    }`}
                  >
                    PARENT
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData({...formData, role: 'Manager'})}
                    className={`py-4 rounded-2xl font-black text-xs transition-all border-2 ${
                      formData.role === 'Manager' 
                      ? 'border-brand-500 bg-brand-50 text-brand-500 shadow-inner' 
                      : 'border-slate-100 text-slate-400'
                    }`}
                  >
                    MANAGER
                  </button>
                </div>
                <div className="flex items-center gap-2 justify-center bg-slate-50 p-3 rounded-xl border border-slate-100 mt-2">
                  <ShieldCheck size={14} className="text-brand-500" />
                  <p className="text-[9px] text-slate-400 font-bold uppercase leading-tight">
                    Teachers must be added by Managers in Settings
                  </p>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand-500 hover:bg-brand-600 text-white font-black py-5 rounded-2xl shadow-xl shadow-brand-500/30 flex items-center justify-center gap-2 mt-4 transition-transform active:scale-95 disabled:opacity-50"
              >
                {loading ? 'PROCESSING...' : 'CONTINUE TO VERIFY'} <ArrowRight size={20} />
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyPhone} className="space-y-6">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-50 text-brand-500 rounded-full mb-2">
                  <Phone size={32} />
                </div>
                <h2 className="text-xl font-black text-slate-800">Verify Phone</h2>
                <p className="text-xs text-slate-500 px-4">
                  Check your terminal logs! Enter the 6-digit verification code sent to <span className="font-bold text-brand-500">{formData.phone}</span>
                </p>
              </div>

              <input
                type="text"
                maxLength="6"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                placeholder="000000"
                className="w-full text-center text-2xl tracking-[0.5em] font-black py-4 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 outline-none"
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
                className="w-full text-brand-500 font-black text-xs uppercase hover:underline"
              >
                Back to Details
              </button>
            </form>
          )}

          {step === 1 && (
            <div className="mt-8 text-center pt-6 border-t border-slate-50">
              <p className="text-slate-400 text-xs font-bold uppercase tracking-widest">
                Already have an account?{' '}
                <Link to="/login" className="text-brand-500 hover:underline">
                  Login Here
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}