import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import AlertBanner from '../../components/common/AlertBanner';
import { LogIn, Key, Mail, ShieldCheck } from 'lucide-react';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid email or password. Please verify credentials.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickFill = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white text-2xl font-black shadow-md">
          E
        </div>
        <h2 className="mt-4 text-3xl font-extrabold text-slate-900 tracking-tight">
          EduTrack Portal
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Student Learning & Activity Management Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-2xl sm:px-10">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && <AlertBanner type="error" message={error} onClose={() => setError('')} />}

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Email Address
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-5 w-5" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@edutrack.org"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Key className="h-5 w-5" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <LogIn className="w-4 h-4 mr-2" />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Quick Fill Demo Roles */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex items-center space-x-1 text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              <ShieldCheck className="w-4 h-4 text-indigo-500" />
              <span>Quick Test Accounts</span>
            </div>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleQuickFill('admin@edutrack.org', 'Password123!')}
                className="w-full text-left px-3 py-2 rounded-lg border border-slate-200 hover:border-purple-300 hover:bg-purple-50/50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-purple-900">Super Admin</span>
                  <p className="text-slate-500 text-[11px]">admin@edutrack.org</p>
                </div>
                <span className="text-[11px] font-medium text-purple-700 bg-purple-100 px-2 py-0.5 rounded">All Centers</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill('manager.north@edutrack.org', 'Password123!')}
                className="w-full text-left px-3 py-2 rounded-lg border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-indigo-900">Center Manager</span>
                  <p className="text-slate-500 text-[11px]">manager.north@edutrack.org</p>
                </div>
                <span className="text-[11px] font-medium text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded">North Hub</span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill('teacher.smith@edutrack.org', 'Password123!')}
                className="w-full text-left px-3 py-2 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 transition-colors flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-semibold text-emerald-900">Teacher (Multi-Center)</span>
                  <p className="text-slate-500 text-[11px]">teacher.smith@edutrack.org</p>
                </div>
                <span className="text-[11px] font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">North & South</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

