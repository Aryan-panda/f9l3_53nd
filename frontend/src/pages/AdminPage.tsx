import React, { useState } from 'react';
import { ShieldCheck, Users, Radio, Activity } from 'lucide-react';
import { AuditLogViewer } from '../components/AuditLogViewer';
import { UserManagementView } from '../components/UserManagementView';
import { NetworkStatusWidget } from '../components/NetworkStatusWidget';

export const AdminPage: React.FC = () => {
  const [subTab, setSubTab] = useState<'audit' | 'users' | 'network'>('audit');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white font-mono tracking-wide">
              ADMINISTRATION & FORENSICS CENTER
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400 font-mono">
              SECURITY OFFICER
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Tamper-evident audit verification, identity mediation, and network security inspection
          </p>
        </div>

        {/* Subtab Switcher */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 font-mono text-xs">
          <button
            onClick={() => setSubTab('audit')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all ${
              subTab === 'audit'
                ? 'bg-slate-800 text-cyan-400 shadow-sm font-semibold border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Audit Forensics</span>
          </button>

          <button
            onClick={() => setSubTab('users')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all ${
              subTab === 'users'
                ? 'bg-slate-800 text-cyan-400 shadow-sm font-semibold border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>User Access</span>
          </button>

          <button
            onClick={() => setSubTab('network')}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all ${
              subTab === 'network'
                ? 'bg-slate-800 text-cyan-400 shadow-sm font-semibold border border-slate-700'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>WireGuard VPN</span>
          </button>
        </div>
      </div>

      {/* Tab Contents */}
      {subTab === 'audit' && <AuditLogViewer />}
      {subTab === 'users' && <UserManagementView />}
      {subTab === 'network' && (
        <div className="space-y-6">
          <NetworkStatusWidget />
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 font-mono text-xs">
            <h4 className="text-slate-200 font-semibold flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>VPN CRYPTOKEY ROUTING & NETWORK POLICY</span>
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Branch-to-branch communication is strictly encapsulated over WireGuard tunnels.
              Each branch node maps public keys directly to AllowedIPs lists (`10.13.37.0/24`).
              Any unauthorized packets outside this point-to-point interface are dropped by the
              kernel prior to reaching application sockets.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
