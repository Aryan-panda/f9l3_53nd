import React from 'react';
import {
  ShieldCheck,
  Radio,
  LogOut,
  Activity,
  Layers,
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  currentTab: 'transfers' | 'admin';
  onTabChange: (tab: 'transfers' | 'admin') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onTabChange }) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono font-bold text-lg text-white tracking-wider">
                  f9l3_53nd
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-700/50 text-cyan-400 font-mono">
                  AES-256-GCM
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Encrypted Branch-to-Branch Secure Transfer
              </p>
            </div>
          </div>

          {/* Center Navigation Tabs */}
          <nav className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => onTabChange('transfers')}
              className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                currentTab === 'transfers'
                  ? 'bg-slate-800 text-cyan-400 shadow-sm border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Transfers</span>
            </button>

            {user?.role === 'ADMIN' && (
              <button
                onClick={() => onTabChange('admin')}
                className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  currentTab === 'admin'
                    ? 'bg-slate-800 text-cyan-400 shadow-sm border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Activity className="w-4 h-4" />
                <span>Admin & Forensics</span>
              </button>
            )}
          </nav>

          {/* Right Status & User Profile */}
          <div className="flex items-center space-x-4">
            {/* WireGuard Status Indicator */}
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-950/50 border border-emerald-800/40 text-emerald-400 text-xs font-mono">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Radio className="w-3.5 h-3.5" />
              <span>WG VPN: 10.13.37.0/24</span>
            </div>

            {/* User Profile Info */}
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-800">
              <div className="text-right">
                <div className="flex items-center justify-end space-x-1.5">
                  <span className="text-xs font-medium text-slate-200">
                    {user?.username}
                  </span>
                  <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                    {user?.role}
                  </span>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {user?.branch || 'Branch Node'}
                </span>
              </div>

              <button
                onClick={logout}
                title="Logout session"
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-rose-950/60 hover:text-rose-400 border border-slate-700 hover:border-rose-800/60 text-slate-400 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
