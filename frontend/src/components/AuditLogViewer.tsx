import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
  Search,
  ChevronDown,
  ChevronUp,
  Fingerprint,
} from 'lucide-react';
import { api } from '../services/api';
import { AuditChainVerification, AuditEvent } from '../types';

export const AuditLogViewer: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [verification, setVerification] = useState<AuditChainVerification | null>(null);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const [filterEventType, setFilterEventType] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    try {
      const res = await api.verifyAuditChain();
      setVerification(res);
    } catch {
      // Error
    } finally {
      setIsVerifying(false);
    }
  };

  useEffect(() => {
    const loadEvents = async () => {
      setLoading(true);
      try {
        const res = await api.getAuditEvents({
          severity: filterSeverity || undefined,
          eventType: filterEventType || undefined,
        });
        setEvents(res.items);
        setTotal(res.total);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
    handleVerifyChain();
  }, [filterSeverity, filterEventType]);



  return (
    <div className="space-y-6">
      {/* Cryptographic Chain Integrity Banner */}
      <div
        className={`p-5 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all ${
          verification?.is_valid
            ? 'bg-emerald-950/20 border-emerald-800/60 shadow-lg shadow-emerald-950/20'
            : verification
            ? 'bg-rose-950/30 border-rose-800 shadow-lg shadow-rose-950/30'
            : 'bg-slate-900 border-slate-800'
        }`}
      >
        <div className="flex items-center space-x-3.5">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              verification?.is_valid
                ? 'bg-emerald-950 border border-emerald-700/60 text-emerald-400'
                : 'bg-rose-950 border border-rose-700/60 text-rose-400'
            }`}
          >
            {verification?.is_valid ? (
              <ShieldCheck className="w-7 h-7" />
            ) : (
              <ShieldAlert className="w-7 h-7" />
            )}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-white font-mono">
                CRYPTOGRAPHIC AUDIT CHAIN STATUS
              </h3>
              {verification?.is_valid ? (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-300 font-mono">
                  HMAC-SHA256 INTACT
                </span>
              ) : (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-950 border border-rose-700 text-rose-300 font-mono">
                  CHAIN TAMPER DETECTED
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              {verification?.message || 'Validating cryptographic chain...'}
            </p>
          </div>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={isVerifying}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-mono shadow-sm transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
          <span>{isVerifying ? 'Recalculating Chain...' : 'Verify Cryptographic Chain'}</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 p-4 rounded-2xl border border-slate-800 font-mono text-xs">
        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="flex items-center space-x-2 text-slate-400">
            <Search className="w-4 h-4" />
            <span>Filter:</span>
          </div>

          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Severities</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="SECURITY_ALERT">SECURITY_ALERT</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>

          <select
            value={filterEventType}
            onChange={(e) => setFilterEventType(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Event Types</option>
            <option value="AUTH_LOGIN_SUCCESS">AUTH_LOGIN_SUCCESS</option>
            <option value="AUTH_LOGIN_FAILURE">AUTH_LOGIN_FAILURE</option>
            <option value="AUTH_LOGOUT">AUTH_LOGOUT</option>
            <option value="TRANSFER_UPLOADED">TRANSFER_UPLOADED</option>
            <option value="TRANSFER_DOWNLOADED">TRANSFER_DOWNLOADED</option>
            <option value="DECRYPTION_FAILURE">DECRYPTION_FAILURE</option>
            <option value="INTEGRITY_MISMATCH">INTEGRITY_MISMATCH</option>
            <option value="PAYLOAD_QUARANTINED">PAYLOAD_QUARANTINED</option>
          </select>
        </div>

        <div className="text-slate-500 text-[11px] self-end sm:self-center">
          Total Log Records: <span className="text-slate-300 font-semibold">{total}</span>
        </div>
      </div>

      {/* Log Entries Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400 font-mono">
            Loading forensic audit events...
          </div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400 font-mono">
            No audit records matching query parameters.
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {events.map((event, idx) => {
              const isExpanded = expandedId === event.id;
              return (
                <div key={event.id} className="p-4 hover:bg-slate-950/40 transition-colors">
                  <div
                    onClick={() => setExpandedId(isExpanded ? null : event.id)}
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-500 font-mono text-[11px] w-6">
                        #{events.length - idx}
                      </span>
                      <span className="text-slate-400 font-mono text-xs">
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                          event.severity === 'CRITICAL'
                            ? 'bg-rose-950 text-rose-300 border border-rose-800'
                            : event.severity === 'WARNING' || event.severity === 'SECURITY_ALERT'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {event.event_type}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="hidden md:flex items-center space-x-1.5 text-slate-500 text-[11px] font-mono">
                        <Fingerprint className="w-3.5 h-3.5 text-cyan-500" />
                        <span>Hash: {event.record_hash.slice(0, 12)}...</span>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Inspector */}
                  {isExpanded && (
                    <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-[11px] space-y-2">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-400">
                        <div>
                          <span className="text-slate-500">Event ID:</span> {event.id}
                        </div>
                        <div>
                          <span className="text-slate-500">Actor ID:</span>{' '}
                          {event.actor_id || 'System / Unauthenticated'}
                        </div>
                        <div>
                          <span className="text-slate-500">Target Resource:</span>{' '}
                          {event.target_resource || 'None'}
                        </div>
                        <div>
                          <span className="text-slate-500">IP Address:</span>{' '}
                          {event.ip_address || 'Internal (127.0.0.1)'}
                        </div>
                      </div>

                      <div className="pt-2 border-t border-slate-800">
                        <span className="text-slate-500 block mb-1">
                          Previous Record Hash Link:
                        </span>
                        <p className="text-slate-400 break-all select-all">
                          {event.prev_record_hash}
                        </p>
                      </div>

                      <div>
                        <span className="text-slate-500 block mb-1">
                          Current Record HMAC-SHA256 Hash:
                        </span>
                        <p className="text-cyan-400 break-all select-all font-semibold">
                          {event.record_hash}
                        </p>
                      </div>

                      <div>
                        <span className="text-slate-500 block mb-1">Event Details:</span>
                        <pre className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-emerald-400 overflow-x-auto">
                          {JSON.stringify(event.details, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
