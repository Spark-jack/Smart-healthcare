import React, { useState } from 'react';
import { Activity, Lock, Mail, HeartPulse, User, Shield, Stethoscope, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage = ({ onSwitchToRegister }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err) {
      console.error("Login failed:", err);
      setError(err.response?.data?.detail || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (userEmail, userPassword) => {
    setEmail(userEmail);
    setPassword(userPassword);
    setLoading(true);
    setError(null);
    try {
      await login(userEmail, userPassword);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to log in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-100 via-teal-50/40 to-slate-200">
      <div className="w-full max-w-md bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-slate-200/80 p-8">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-teal-600 to-emerald-500 mx-auto flex items-center justify-center text-white shadow-lg shadow-teal-600/30 mb-3">
            <HeartPulse className="w-8 h-8 stroke-[2.2]" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900">
            SmartHealth<span className="text-teal-600">.AI</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Predictive Clinical Risk Engine & Urgency Triage
          </p>
        </div>

        {error && (
          <div className="mb-5 p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@hospital.org"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 transition disabled:opacity-50 mt-2"
          >
            {loading ? 'Authenticating...' : 'Sign In to Portal'}
          </button>
        </form>

        {/* 1-Click Demo Accounts */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block text-center mb-3">
            Quick 1-Click Role Login (Sample Accounts)
          </span>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={() => quickLogin('dr.eleanor@hospital.org', 'password123')}
              className="p-2.5 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 hover:border-teal-300 text-left transition flex items-center gap-2 text-slate-700 font-semibold"
            >
              <Stethoscope className="w-4 h-4 text-teal-600 shrink-0" />
              <div>
                <span className="block text-[11px] font-bold">Dr. Eleanor</span>
                <span className="text-[9px] text-slate-400">Cardiologist</span>
              </div>
            </button>

            <button
              onClick={() => quickLogin('arthur.pendelton@patient.com', 'password123')}
              className="p-2.5 rounded-xl bg-slate-50 hover:bg-rose-50 border border-slate-200 hover:border-rose-300 text-left transition flex items-center gap-2 text-slate-700 font-semibold"
            >
              <User className="w-4 h-4 text-rose-500 shrink-0" />
              <div>
                <span className="block text-[11px] font-bold">Arthur P.</span>
                <span className="text-[9px] text-rose-500 font-bold">Critical Risk</span>
              </div>
            </button>

            <button
              onClick={() => quickLogin('liam.foster@patient.com', 'password123')}
              className="p-2.5 rounded-xl bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 text-left transition flex items-center gap-2 text-slate-700 font-semibold"
            >
              <User className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <span className="block text-[11px] font-bold">Liam Foster</span>
                <span className="text-[9px] text-emerald-600 font-bold">Routine / Low</span>
              </div>
            </button>

            <button
              onClick={() => quickLogin('admin@hospital.org', 'admin123')}
              className="p-2.5 rounded-xl bg-slate-50 hover:bg-purple-50 border border-slate-200 hover:border-purple-300 text-left transition flex items-center gap-2 text-slate-700 font-semibold"
            >
              <Shield className="w-4 h-4 text-purple-600 shrink-0" />
              <div>
                <span className="block text-[11px] font-bold">Admin Portal</span>
                <span className="text-[9px] text-slate-400">System Admin</span>
              </div>
            </button>
          </div>
        </div>

        {/* Register switch link */}
        <div className="mt-6 text-center text-xs text-slate-500">
          New patient or clinical staff?{' '}
          <button
            onClick={onSwitchToRegister}
            className="text-teal-600 font-bold hover:underline"
          >
            Create an Account
          </button>
        </div>

      </div>
    </div>
  );
};
