/* ============================================================================
   RegisterPage — User Account Creation Screen
   ============================================================================ */

import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Lock, Mail, User, ArrowRight, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const RegisterPage = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { register, loading, error, setError } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password) {
      setError('Please fill out all fields.');
      return;
    }
    try {
      await register({ full_name: fullName, email, password });
      navigate('/dashboard', { replace: true });
    } catch {
      // Error handled by hook
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-6 md:p-10 bg-[#06080F] relative overflow-hidden">
      {/* Background ambient glow spots */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-gradient-to-tr from-cyan/15 via-violet/10 to-transparent blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute -bottom-20 -right-20 w-[450px] h-[450px] bg-cyan/5 blur-[140px] pointer-events-none rounded-full" />

      {/* Main Register Card */}
      <div className="w-full max-w-[480px] bg-[#0E1424]/90 backdrop-blur-2xl border border-white/[0.1] rounded-3xl p-9 md:p-12 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.8),0_0_40px_rgba(0,229,255,0.06)] animate-fade-in relative overflow-hidden z-10">
        {/* Top subtle cyan glow line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan/60 to-transparent" />

        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan via-[#00E5FF] to-violet inline-flex items-center justify-center mb-5 shadow-[0_0_28px_rgba(0,229,255,0.4)]">
            <Sparkles size={28} className="text-black" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Create Account</h1>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed">
            Start analyzing operations with the AI Agent
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl py-3 px-4 text-rose-400 text-xs mb-6">
            <AlertCircle size={16} className="shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Full Name
            </label>
            <div className="flex items-center gap-3 bg-white/[0.03] border border-white/10 rounded-xl py-3.5 px-4 focus-within:border-cyan/60 focus-within:bg-white/[0.05] focus-within:shadow-[0_0_20px_rgba(0,229,255,0.18)] transition-all">
              <User size={18} className="text-slate-400 shrink-0" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                className="flex-1 bg-transparent border-none outline-none text-white text-sm placeholder:text-slate-500 font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Work Email
            </label>
            <div className="flex items-center gap-3 bg-white/[0.03] border border-white/10 rounded-xl py-3.5 px-4 focus-within:border-cyan/60 focus-within:bg-white/[0.05] focus-within:shadow-[0_0_20px_rgba(0,229,255,0.18)] transition-all">
              <Mail size={18} className="text-slate-400 shrink-0" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="flex-1 bg-transparent border-none outline-none text-white text-sm placeholder:text-slate-500 font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="flex items-center gap-3 bg-white/[0.03] border border-white/10 rounded-xl py-3.5 px-4 focus-within:border-cyan/60 focus-within:bg-white/[0.05] focus-within:shadow-[0_0_20px_rgba(0,229,255,0.18)] transition-all">
              <Lock size={18} className="text-slate-400 shrink-0" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="flex-1 bg-transparent border-none outline-none text-white text-sm placeholder:text-slate-500 font-medium"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-2 flex items-center justify-center gap-2.5 bg-gradient-to-r from-cyan via-[#00E5FF] to-violet text-black border-none rounded-xl py-4 px-6 text-sm uppercase tracking-wider font-bold cursor-pointer transition-all duration-200 shadow-[0_0_24px_rgba(0,229,255,0.3)] hover:shadow-[0_0_36px_rgba(0,229,255,0.5)] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>{loading ? 'Creating...' : 'Register Account'}</span>
            {!loading && <ArrowRight size={17} />}
          </button>
        </form>

        <div className="text-center mt-8 pt-6 border-t border-white/[0.06] text-xs text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-cyan no-underline font-semibold hover:underline ml-1">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
