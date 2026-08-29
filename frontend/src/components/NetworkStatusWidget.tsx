import React, { useState, useEffect } from 'react';
import { Radio, RefreshCw, Server, ArrowRightLeft } from 'lucide-react';
import { api } from '../services/api';
import { TunnelStatus } from '../types';

export const NetworkStatusWidget: React.FC = () => {
  const [tunnel, setTunnel] = useState<TunnelStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await api.getNetworkStatus();
      setTunnel(res);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 font-mono">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center text-emerald-400">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              WIREGUARD P2P TUNNEL TOPOLOGY
            </h3>
            <p className="text-[11px] text-slate-400">
              Point-to-Point Overlay Network (10.13.37.0/24)
            </p>
          </div>
        </div>

        <button
          onClick={fetchStatus}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Network Nodes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
        {/* Branch A Node */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <Server className="w-4 h-4 text-cyan-400" />
              <span>BRANCH A (HQ)</span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
              LOCAL
            </span>
          </div>
          <div className="text-[11px] space-y-1 text-slate-400">
            <div>
              <span className="text-slate-500">Overlay IP:</span> {tunnel?.local_ip || '10.13.37.1'}
            </div>
            <div>
              <span className="text-slate-500">Interface:</span> {tunnel?.interface || 'wg0'}
            </div>
            <div>
              <span className="text-slate-500">Port:</span> 51820
            </div>
          </div>
        </div>

        {/* Center Interconnect Link */}
        <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center space-y-1">
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold">
            <ArrowRightLeft className="w-4 h-4" />
            <span>ENCRYPTED LINK</span>
          </div>
          <div className="text-[10px] text-slate-400">
            Curve25519 + ChaCha20-Poly1305
          </div>
          <div className="text-[10px] text-emerald-500 flex items-center space-x-1">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Handshake: {tunnel?.latest_handshake_seconds_ago || 15}s ago</span>
          </div>
        </div>

        {/* Branch B Node */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
              <Server className="w-4 h-4 text-emerald-400" />
              <span>BRANCH B (REMOTE)</span>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300">
              PEER
            </span>
          </div>
          <div className="text-[11px] space-y-1 text-slate-400">
            <div>
              <span className="text-slate-500">Overlay IP:</span> {tunnel?.peer_ip || '10.13.37.2'}
            </div>
            <div>
              <span className="text-slate-500">Endpoint:</span>{' '}
              {tunnel?.peer_endpoint || '127.0.0.1:51821'}
            </div>
            <div>
              <span className="text-slate-500">Keepalive:</span> 25s
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
