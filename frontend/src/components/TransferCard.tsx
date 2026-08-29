import React, { useState } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Copy,
  Check,
  ArrowRight,
} from 'lucide-react';
import { Transfer } from '../types';
import { api } from '../services/api';

interface TransferCardProps {
  transfer: Transfer;
  currentUserId?: string;
  onRefresh: () => void;
}

export const TransferCard: React.FC<TransferCardProps> = ({
  transfer,
  currentUserId,
  onRefresh,
}) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const isSender = transfer.sender_id === currentUserId;
  const isQuarantined = transfer.state === 'QUARANTINED';
  const isCompleted = transfer.state === 'COMPLETED';

  const copyDigest = () => {
    navigator.clipboard.writeText(transfer.original_sha256);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    setDownloadError(null);
    try {
      await api.downloadTransfer(transfer.id, transfer.filename);
      onRefresh();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setDownloadError(err.message);
      } else {
        setDownloadError('Failed to decrypt and verify payload.');
      }
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div
      className={`rounded-2xl border p-5 transition-all ${
        isQuarantined
          ? 'bg-rose-950/20 border-rose-800/50 shadow-lg shadow-rose-950/20'
          : isCompleted
          ? 'bg-slate-900/90 border-slate-800 hover:border-emerald-700/50'
          : 'bg-slate-900 border-slate-800 hover:border-cyan-700/50'
      }`}
    >
      {/* Top Bar: Filename & State Badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              isQuarantined
                ? 'bg-rose-950 text-rose-400 border border-rose-800/60'
                : isCompleted
                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                : 'bg-cyan-950/80 text-cyan-400 border border-cyan-800/60'
            }`}
          >
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white tracking-wide">
              {transfer.filename}
            </h4>
            <span className="text-xs text-slate-400 font-mono">
              {(transfer.file_size / 1024).toFixed(2)} KB •{' '}
              {new Date(transfer.created_at).toLocaleTimeString()}
            </span>
          </div>
        </div>

        {/* State Badge */}
        <div className="flex items-center space-x-1.5">
          {isQuarantined ? (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium bg-rose-950 border border-rose-700/60 text-rose-300">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              <span>QUARANTINED</span>
            </span>
          ) : isCompleted ? (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium bg-emerald-950 border border-emerald-700/60 text-emerald-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>VERIFIED & DELIVERED</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium bg-cyan-950 border border-cyan-700/60 text-cyan-300">
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              <span>ENCRYPTED (AES-256-GCM)</span>
            </span>
          )}
        </div>
      </div>

      {/* Origin -> Destination Flow */}
      <div className="flex items-center space-x-2 my-3 py-2 px-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs font-mono">
        <span
          className={`px-2 py-0.5 rounded text-[10px] ${
            isSender
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
              : 'bg-slate-800 text-slate-300'
          }`}
        >
          {isSender ? 'YOU (Sender)' : 'Sender'}
        </span>
        <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
        <span
          className={`px-2 py-0.5 rounded text-[10px] ${
            !isSender
              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
              : 'bg-slate-800 text-slate-300'
          }`}
        >
          {!isSender ? 'YOU (Recipient)' : 'Recipient'}
        </span>
        <span className="ml-auto text-[11px] text-slate-500">
          UUID: {transfer.id.slice(0, 8)}...
        </span>
      </div>

      {/* SHA-256 Digest Box */}
      <div className="mt-3 p-2.5 rounded-xl bg-slate-950/90 border border-slate-800 font-mono text-[11px] space-y-1">
        <div className="flex items-center justify-between text-slate-400">
          <span>ORIGINAL SHA-256 GROUND TRUTH:</span>
          <button
            onClick={copyDigest}
            className="flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        <p className="text-slate-300 break-all select-all">
          {transfer.original_sha256}
        </p>

        {transfer.decrypted_sha256 && (
          <div className="pt-1.5 border-t border-slate-800 flex items-center justify-between text-emerald-400">
            <span>VERIFIED DECRYPTED SHA-256:</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800/50">
              MATCH CONFIRMED
            </span>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {downloadError && (
        <div className="mt-3 p-2.5 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs font-mono">
          {downloadError}
        </div>
      )}

      {/* Bottom Download & Verification Action */}
      <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800/60">
        <div className="text-[11px] text-slate-500 font-mono">
          {transfer.completed_at ? (
            <span>Completed at {new Date(transfer.completed_at).toLocaleTimeString()}</span>
          ) : (
            <span>Ready for verified download</span>
          )}
        </div>

        <button
          onClick={handleDownload}
          disabled={isDownloading || isQuarantined}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold font-mono transition-all ${
            isQuarantined
              ? 'bg-rose-950/40 border border-rose-800 text-rose-400 cursor-not-allowed'
              : 'bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-700/60 hover:border-cyan-500 shadow-sm'
          }`}
        >
          {isDownloading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
              <span>Verifying & Decrypting...</span>
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              <span>
                {isQuarantined ? 'Quarantined (Tampered)' : 'Decrypt & Download'}
              </span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
