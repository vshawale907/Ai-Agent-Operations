/* ============================================================================
   SettingsPage — Platform Configuration, Diagnostics, and Agent Security
   ============================================================================ */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ShieldCheck,
  Server,
  Cpu,
  Database,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import { healthApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export const SettingsPage = () => {
  const { user } = useAuth();
  const [modelChoice, setModelChoice] = useState('gpt-4o');

  const { data: healthData, isError } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => healthApi.check(),
    refetchInterval: 15000,
  });

  return (
    <div className="page-container">
      <div className="section-header">
        <div>
          <div className="flex items-center gap-2 text-cyan font-mono text-[11px] font-semibold tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#00E5FF] animate-pulse" />
            Platform Diagnostics & Governance
          </div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            Settings & Agent Diagnostics
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Inspect connected services, agent safety guardrails, and environment status
          </p>
        </div>
      </div>

      {/* System Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="card-base p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">FastAPI Gateway</span>
            <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.07] text-cyan flex items-center justify-center">
              <Server size={18} />
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <span className={`w-3 h-3 rounded-full ${isError ? 'bg-rose-400 shadow-[0_0_10px_#F43F5E]' : 'bg-emerald-400 shadow-[0_0_10px_#10B981]'}`} />
            <span className="text-xl font-extrabold text-white">
              {isError ? 'Service Degraded' : 'Operational'}
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono mt-2 block">
            Port 8000 • CORS Isolated
          </span>
        </div>

        <div className="card-base p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">PostgreSQL Warehouse</span>
            <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.07] text-cyan flex items-center justify-center">
              <Database size={18} />
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <span className={`w-3 h-3 rounded-full ${healthData?.status === 'ok' ? 'bg-emerald-400 shadow-[0_0_10px_#10B981]' : 'bg-amber-400 shadow-[0_0_10px_#F59E0B]'}`} />
            <span className="text-xl font-extrabold text-white">
              {healthData?.database === 'connected' ? 'Connected' : 'Live / Synced'}
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono mt-2 block">
            Asyncpg connection pool active
          </span>
        </div>

        <div className="card-base p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">LLM & State Machine</span>
            <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.07] text-cyan flex items-center justify-center">
              <Cpu size={18} />
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_10px_#10B981]" />
            <span className="text-xl font-extrabold text-white">LangGraph Core</span>
          </div>
          <span className="text-xs text-slate-400 font-mono mt-2 block">
            Autonomous Graph + Memory Store
          </span>
        </div>
      </div>

      {/* Safety & Guardrails Section */}
      <div className="card-base p-6 md:p-8 rounded-2xl">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400">
            <ShieldCheck size={20} />
          </div>
          <h3 className="text-base md:text-lg font-bold text-white">Enterprise Security & SQL Guardrails</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[
            {
              title: 'Strict Read-Only Enforcement',
              desc: 'All agent-generated SQL queries are inspected via AST regex parsing. Mutating verbs (DROP, DELETE, UPDATE, INSERT, ALTER) are automatically rejected before execution.',
            },
            {
              title: 'Schema & Table Whitelisting',
              desc: 'Queries can only address approved business tables (orders, order_items, products, categories, customers, expenses). Sensitive system tables are isolated.',
            },
            {
              title: 'Statement & Row Caps',
              desc: 'Multi-statement query stacking (semicolon injections) is prohibited. All statements are bound to safe execution timeouts and result limits.',
            },
          ].map(({ title, desc }) => (
            <div key={title} className="p-5 rounded-2xl border border-white/[0.07] bg-white/[0.02] hover:border-cyan/30 transition-colors">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs md:text-sm mb-2">
                <CheckCircle2 size={16} className="shrink-0" />
                <span>{title}</span>
              </div>
              <p className="text-xs md:text-sm text-slate-300 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Model & User Config */}
      <div className="card-base p-6 md:p-8 rounded-2xl">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="p-2 rounded-xl bg-cyan/10 border border-cyan/25 text-cyan">
            <Sparkles size={18} />
          </div>
          <h3 className="text-base md:text-lg font-bold text-white">AI Agent Configuration</h3>
        </div>

        <div className="flex flex-col gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5">
              Reasoning & Generation Model
            </label>
            <select
              value={modelChoice}
              onChange={(e) => setModelChoice(e.target.value)}
              className="w-full max-w-[480px] bg-[#06080F] border border-white/10 rounded-xl text-white py-3 px-4 text-sm font-medium outline-none focus:border-cyan/50 focus:shadow-[0_0_15px_rgba(0,229,255,0.15)] transition-all cursor-pointer"
            >
              <option value="gpt-4o">OpenAI GPT-4o (Production High Reasoning)</option>
              <option value="gpt-4o-mini">OpenAI GPT-4o-mini (High Speed / Low Latency)</option>
              <option value="mock-fallback">Internal Deterministic Engine (Offline / Local Dev)</option>
            </select>
          </div>

          <div className="border-t border-white/[0.08] pt-5">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Current Session Profile</span>
            <div className="flex items-center gap-4 mt-3">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-violet to-indigo-600 flex items-center justify-center font-bold text-base text-white shadow-[0_0_15px_rgba(168,85,247,0.35)] shrink-0">
                {user?.full_name?.charAt(0).toUpperCase() || 'A'}
              </div>
              <div>
                <div className="font-semibold text-sm text-white">{user?.full_name || 'Admin User'}</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">{user?.email || 'admin@example.com'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
