import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, Phone } from 'lucide-react';
import axiosInstance from '../api/axiosInstance';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Teacher-only verification step
  const [requiresPhoneVerification, setRequiresPhoneVerification] = useState(false);
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [requesting, setRequesting] = useState(false);

  const navigate = useNavigate();

  const normalizeIsTeacher = (roleRaw) => {
    const r = Array.isArray(roleRaw)
      ? roleRaw.map((x) => String(x).trim().toLowerCase())
      : String(roleRaw ?? '').trim().toLowerCase();
    return Array.isArray(r) ? r.includes('teacher') : r === 'teacher';
  };

  const normalizeBool = (v) =>
    v === true || v === 1 || (typeof v === 'string' && v.toLowerCase() === 'true');

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
      const res = await axiosInstance.post('/auth/login', { email, password });
      const { access_token, role } = res.data || {};

      if (!access_token) {
        setError('Login failed: no token received.');
        return;
      }

      // Store token immediately and dispatch profile fetch in parallel
      localStorage.setItem('token', access_token);
      sessionStorage.setItem('token', access_token);

      const basicUser = { email, role: String(role || '').toLowerCase() };
      localStorage.setItem('user', JSON.stringify(basicUser));
      sessionStorage.setItem('user', JSON.stringify(basicUser));

      const profileFetch = axiosInstance.get('/users/me')
        .then((meRes) => {
          const roleRaw = meRes.data?.role ?? meRes.data?.role_name ?? role;
          const phoneVerified = normalizeBool(meRes.data?.phone_verified);
          const phoneNumber = meRes.data?.phone_number || '';

          // Update cached user with full profile
          const enrichedPayload = {
            email,
            role: Array.isArray(roleRaw)
              ? roleRaw.map((x) => String(x).toLowerCase())
              : String(roleRaw || '').toLowerCase(),
            phone_verified: !!phoneVerified,
            phone_number: phoneNumber || null
          };
          localStorage.setItem('user', JSON.stringify(enrichedPayload));
          sessionStorage.setItem('user', JSON.stringify(enrichedPayload));

          // Return profile info for phone verification check
          return { roleRaw, phoneVerified, phoneNumber, isTeacher: normalizeIsTeacher(roleRaw) };
        })
        .catch((fetchErr) => {
          console.error('Fetch /users/me failed (non-critical):', fetchErr);
          return null;
        });

      // Check if teacher needs phone verification WHILE profile is fetching
      const isTeacher = normalizeIsTeacher(role);
      
      // If teacher, gate phone verification BEFORE profile fetch completes
      if (isTeacher) {
        // We need profile to know if verified, so await but with tight timeout
        const profileData = await Promise.race([
          profileFetch,
          new Promise((resolve) => setTimeout(() => resolve(null), 5000)) // 5-second timeout
        ]);

        if (profileData?.isTeacher && !profileData?.phoneVerified) {
          setRequiresPhoneVerification(true);
          setPhone(profileData.phoneNumber || '');

          // Request code in background - fire and forget
          setRequesting(true);
          axiosInstance.post('/auth/phone/request-code')
            .then(() => {
              console.log('OTP request dispatched');
            })
            .catch((e) => {
              console.error('OTP request failed (user can retry):', e);
            })
            .finally(() => {
              setRequesting(false);
            });

          setLoading(false);
          return;
        }
      }

      // Everyone else navigates immediately
      navigate('/', { replace: true });
    } catch (err) {
      console.error('Login error:', err);
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

  // Request code
  const handleRequestCode = async () => {
    setError('');
    if (!phone) {
      setError('Enter your phone number first.');
      return;
    }
    setRequesting(true);
    try {
      await axiosInstance.post('/auth/phone/request-code', { phone_number: phone });
    } catch (err) {
      console.error('Request code error:', err);
      const msg = err?.response?.data?.detail || 'Could not send code. Try again.';
      setError(typeof msg === 'string' ? msg : 'Could not send code. Try again.');
    } finally {
      setRequesting(false);
    }
  };

  // Verify code
  const handleVerifyPhone = async (e) => {
    e.preventDefault();
    setError('');

    if (!phone || !code) {
      setError('Please provide your phone number and verification code.');
      return;
    }

    setVerifying(true);
    try {
      const codeClean = String(code).trim();

      const qs = `?code=${encodeURIComponent(codeClean)}`;
      await axiosInstance.post(`/auth/phone/verify-code${qs}`);

      // Update cached user to verified before navigating
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      u.phone_verified = true;
      u.phone_number = phone;
      localStorage.setItem('user', JSON.stringify(u));
      sessionStorage.setItem('user', JSON.stringify(u));

      navigate('/', { replace: true });
    } catch (err) {
      console.error('Verify code error:', err);
      const status = err?.response?.status;
      const backendDetail = err?.response?.data?.detail;

      let msg;
      if (typeof backendDetail === 'string') msg = backendDetail;
      else if (Array.isArray(backendDetail)) msg = backendDetail[0]?.msg;

      if (!msg) {
        msg = status === 400 ? 'Invalid or expired verification code.' : 'Unable to verify phone at this time.';
      }
      setError(msg);
    } finally {
      setVerifying(false);
    }
  };

  // Consistent input font helper classes
  const inputBase = 'w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 transition text-slate-800 placeholder-slate-400';

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
            {requiresPhoneVerification ? 'Verify Your Phone' : 'Welcome Back'}
          </h2>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold transition-all">
              {error}
            </div>
          )}

          {!requiresPhoneVerification ? (
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
            <form onSubmit={handleVerifyPhone} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Phone Number</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3.5 text-slate-400" size={20} />
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+966 5x xxx xxxx"
                    className={`w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 transition text-slate-800 placeholder-slate-400`}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Verification Code</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Enter the code sent to your phone"
                  className={inputBase}
                  inputMode="numeric"
                  pattern="[0-9]*"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={verifying}
                className="w-full bg-brand-500 hover:bg-brand-600 text-white font-semibold py-3.5 rounded-xl transition duration-200 disabled:opacity-50 shadow-md shadow-brand-500/20 active:scale-[0.98]"
              >
                {verifying ? 'Verifying...' : 'Verify & Continue'}
              </button>

              <div className="text-center">
                <button
                  type="button"
                  className="mt-3 text-sm text-brand-500 hover:text-brand-600 font-medium"
                  onClick={handleRequestCode}
                  disabled={requesting}
                >
                  {requesting ? 'Sending…' : 'Resend code'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}