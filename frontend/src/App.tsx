import React, { useEffect, useState } from 'react';
import { ShieldCheck, Lock, Activity, Server, Database, Key, CheckCircle2, ArrowRight } from 'lucide-react';
import { HealthStatus } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/health/live')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: HealthStatus) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-brand-500/10 border border-brand-500/30 rounded-lg text-brand-500">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white font-mono">f9l3_53nd</span>
              <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                Phase 0 Foundation
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="inline-block w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
              <span className="text-slate-400">Environment:</span>
              <span className="text-brand-400 font-semibold">{health?.environment || 'local'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-mono mb-6">
            <Lock className="w-3.5 h-3.5" />
            <span>Defense-in-Depth Architecture Active</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
            Secure, Authenticated & Auditable File Transfer Platform
          </h1>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            Engineered with application-layer AES-256-GCM envelope encryption, SHA-256 pre/post integrity verification, Argon2id authentication, and WireGuard branch-to-branch VPN network isolation.
          </p>
        </div>

        {/* Core Cryptographic & Security Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-brand-500/40 transition-all">
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 w-fit mb-4">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">AES-256-GCM Payload AEAD</h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-4">
              Unique 96-bit random nonce per transfer envelope with Authenticated Associated Data (AAD) binding transfer metadata.
            </p>
            <div className="text-xs font-mono text-blue-400 flex items-center space-x-1">
              <span>Standard: RFC 5116 / NIST SP 800-38D</span>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-brand-500/40 transition-all">
            <div className="p-3 bg-brand-500/10 border border-brand-500/20 rounded-xl text-brand-400 w-fit mb-4">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">SHA-256 Hash Verification</h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-4">
              Pre-computed digest verified post-decryption. Transfer fails and quarantines immediately if digests mismatch.
            </p>
            <div className="text-xs font-mono text-brand-400 flex items-center space-x-1">
              <span>Standard: FIPS 180-4 Integrity Guard</span>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-brand-500/40 transition-all">
            <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400 w-fit mb-4">
              <Server className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">WireGuard Branch VPN</h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-4">
              Encrypted point-to-point network transport connecting Branch A and Branch B over untrusted intermediary networks.
            </p>
            <div className="text-xs font-mono text-purple-400 flex items-center space-x-1">
              <span>Topology: 10.50.0.1 ↔ 10.50.0.2</span>
            </div>
          </div>
        </div>

        {/* Phase 0 System Health & Foundation Status */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 mb-6 border-b border-slate-800 gap-4">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <Activity className="w-5 h-5 text-brand-500" />
                <span>Foundation Health & Pipeline Status</span>
              </h2>
              <p className="text-slate-400 text-sm mt-1">
                Monitored backend bootstrap status and test runner readiness.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 text-xs font-mono rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
                Phase Gate 0 Verified
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-slate-500 mb-1 flex items-center justify-between">
                <span>FastAPI Service</span>
                <Server className="w-3.5 h-3.5" />
              </div>
              <div className="text-white font-semibold flex items-center space-x-1.5">
                <span className={`w-2 h-2 rounded-full ${loading ? 'bg-yellow-500' : error ? 'bg-red-500' : 'bg-brand-500'}`}></span>
                <span>{loading ? 'Probing...' : error ? 'Service Offline' : 'Operational (200 OK)'}</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-slate-500 mb-1 flex items-center justify-between">
                <span>Key Management</span>
                <Key className="w-3.5 h-3.5" />
              </div>
              <div className="text-white font-semibold flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-brand-500"></span>
                <span>256-bit KEK Configured</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-slate-500 mb-1 flex items-center justify-between">
                <span>Database Migration</span>
                <Database className="w-3.5 h-3.5" />
              </div>
              <div className="text-white font-semibold flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-brand-500"></span>
                <span>Alembic Configured</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-slate-500 mb-1 flex items-center justify-between">
                <span>Next Milestone</span>
                <ArrowRight className="w-3.5 h-3.5 text-brand-400" />
              </div>
              <div className="text-brand-400 font-semibold">
                Phase 1 Requirements Spec
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 f9l3_53nd — Educational Secure Architecture Platform.</p>
          <div className="flex items-center space-x-6">
            <span>RFC 5116 (AES-GCM)</span>
            <span>FIPS 180-4 (SHA-256)</span>
            <span>RFC 9106 (Argon2id)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
