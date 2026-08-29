import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileCheck2,
  Lock,
  AlertTriangle,
  Radio,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import { Transfer } from '../types';
import { useAuth } from '../context/AuthContext';
import { TransferCard } from '../components/TransferCard';
import { TransferUploadModal } from '../components/TransferUploadModal';
import { NetworkStatusWidget } from '../components/NetworkStatusWidget';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<'all' | 'received' | 'sent' | 'quarantined'>('all');

  const fetchTransfers = async () => {
    setLoading(true);
    try {
      const res = await api.getTransfers();
      setTransfers(res.items);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransfers();
  }, []);

  const totalTransfers = transfers.length;
  const completedCount = transfers.filter((t) => t.state === 'COMPLETED').length;
  const quarantinedCount = transfers.filter((t) => t.state === 'QUARANTINED').length;
  const pendingCount = transfers.filter((t) => t.state === 'ENCRYPTED').length;

  const filteredTransfers = transfers.filter((t) => {
    if (activeFilter === 'received') return t.recipient_id === user?.id;
    if (activeFilter === 'sent') return t.sender_id === user?.id;
    if (activeFilter === 'quarantined') return t.state === 'QUARANTINED';
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner & Main Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white font-mono tracking-wide">
            BRANCH FILE TRANSFER DASHBOARD
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            End-to-end encrypted payload pipeline guarded by AES-256-GCM and WireGuard VPN
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchTransfers}
            disabled={loading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-mono shadow-lg shadow-cyan-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Send Encrypted File</span>
          </button>
        </div>
      </div>

      {/* Metrics Overview Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono">
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>TOTAL TRANSFERS</span>
            <UploadCloud className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-white">{totalTransfers}</p>
          <span className="text-[10px] text-slate-500">Processed through pipeline</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>VERIFIED DELIVERIES</span>
            <FileCheck2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-400">{completedCount}</p>
          <span className="text-[10px] text-slate-500">SHA-256 matching ground truth</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>PENDING ENCRYPTED</span>
            <Lock className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-cyan-400">{pendingCount}</p>
          <span className="text-[10px] text-slate-500">Awaiting receiver verification</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>QUARANTINED</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-bold text-rose-400">{quarantinedCount}</p>
          <span className="text-[10px] text-slate-500">Tamper detection triggered</span>
        </div>
      </div>

      {/* Network Widget */}
      <NetworkStatusWidget />

      {/* Transfer Pipeline Section */}
      <div className="space-y-4">
        {/* Subheader & Filter Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2 font-mono">
            <Radio className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200">
              PAYLOAD PIPELINE QUEUE
            </h3>
            <span className="text-xs text-slate-500">({filteredTransfers.length})</span>
          </div>

          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800 font-mono text-xs">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeFilter === 'all'
                  ? 'bg-slate-800 text-cyan-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setActiveFilter('received')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeFilter === 'received'
                  ? 'bg-slate-800 text-cyan-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Received
            </button>
            <button
              onClick={() => setActiveFilter('sent')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeFilter === 'sent'
                  ? 'bg-slate-800 text-cyan-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sent
            </button>
            <button
              onClick={() => setActiveFilter('quarantined')}
              className={`px-3 py-1 rounded-lg transition-colors ${
                activeFilter === 'quarantined'
                  ? 'bg-slate-800 text-rose-400 font-medium'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Quarantined
            </button>
          </div>
        </div>

        {/* Transfers List */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 font-mono bg-slate-900 rounded-2xl border border-slate-800">
            Scanning encrypted transfer storage...
          </div>
        ) : filteredTransfers.length === 0 ? (
          <div className="p-12 text-center space-y-3 bg-slate-900 rounded-2xl border border-slate-800">
            <UploadCloud className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400 font-mono">
              No file transfers found for this filter view.
            </p>
            <button
              onClick={() => setIsUploadOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-400 font-mono border border-slate-700 transition-colors"
            >
              Send First Encrypted File
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTransfers.map((transfer) => (
              <TransferCard
                key={transfer.id}
                transfer={transfer}
                currentUserId={user?.id}
                onRefresh={fetchTransfers}
              />
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <TransferUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={fetchTransfers}
      />
    </div>
  );
};
