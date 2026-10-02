/* ============================================================================
   Sidebar Layout — Cyber-Executive Application Shell
   ============================================================================ */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  FileText,
  FileSpreadsheet,
  Settings,
  LogOut,
  Sparkles,
  Menu,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/ai', icon: MessageSquare, label: 'AI Chat' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/documents', icon: FileText, label: 'Knowledge Base' },
  { to: '/reports', icon: FileSpreadsheet, label: 'Reports' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-[#06080F] text-slate-100 overflow-x-hidden">
      {/* Mobile menu trigger */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed top-4 left-4 z-50 bg-[#0E1424] border border-white/10 rounded-xl p-2.5 text-slate-200 cursor-pointer md:hidden shadow-lg hover:border-cyan/40 transition-colors"
        aria-label="Toggle Navigation"
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-30 md:hidden animate-fade-in"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-screen z-40 flex flex-col bg-[#080C16]/98 backdrop-blur-2xl border-r border-white/[0.08] transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
        style={{ width: 'var(--sidebar-width)' }}
      >
        {/* Brand / Logo */}
        <div className="px-6 py-5 border-b border-white/[0.08] flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan via-[#00E5FF] to-violet flex items-center justify-center shadow-[0_0_20px_rgba(0,229,255,0.35)] shrink-0 ring-1 ring-white/20">
            <Sparkles size={20} className="text-black" />
          </div>
          <div className="min-w-0">
            <div className="font-bold text-[15px] text-white tracking-tight flex items-center gap-1.5 font-display">
              BizAgent AI
            </div>
            <div className="text-[10px] text-cyan font-mono tracking-widest uppercase mt-0.5 font-medium flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan shadow-[0_0_6px_#00E5FF]" />
              Operations Intelligence
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 py-5 px-3 flex flex-col gap-1.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3.5 h-11 px-3.5 rounded-xl no-underline text-sm transition-all duration-200 group relative ${
                  isActive
                    ? 'text-cyan bg-cyan/[0.08] border border-cyan/25 shadow-[0_0_18px_rgba(0,229,255,0.08)] font-semibold'
                    : 'text-slate-300 border border-transparent font-medium hover:text-white hover:bg-white/[0.04]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={19}
                    className={`shrink-0 transition-transform duration-200 group-hover:scale-105 ${
                      isActive ? 'text-cyan' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  <span className="truncate">{label}</span>
                  {isActive && (
                    <span className="absolute right-3 w-1.5 h-1.5 rounded-full bg-cyan shadow-[0_0_8px_#00E5FF]" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User Info & Session Controls */}
        <div className="px-5 py-4 border-t border-white/[0.08] flex items-center gap-3 bg-white/[0.01]">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet to-indigo-600 text-white font-bold flex items-center justify-center text-xs shadow-[0_0_14px_rgba(168,85,247,0.35)] shrink-0 ring-1 ring-white/10">
            {user?.full_name?.charAt(0).toUpperCase() || 'O'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-slate-100 truncate">
              {user?.full_name || 'Operations Admin'}
            </div>
            <div className="text-[11px] text-slate-400 truncate font-mono mt-0.5">
              {user?.email || 'admin@example.com'}
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer border-none bg-transparent shrink-0"
            title="Sign Out"
            aria-label="Sign Out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main
        className="flex-1 min-w-0 w-full overflow-y-auto overflow-x-hidden"
        style={{
          marginLeft: 'var(--sidebar-width)',
          padding: 'var(--content-padding-y) var(--content-padding-x)',
        }}
      >
        <Outlet />
      </main>

      {/* Mobile: reset margin */}
      <style>{`
        @media (max-width: 767px) {
          main {
            margin-left: 0 !important;
          }
        }
      `}</style>
    </div>
  );
}
