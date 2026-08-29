import React, { useState, useEffect } from 'react';
import {
  X,
  Upload,
  FileText,
  Lock,
  Cpu,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

interface TransferUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const TransferUploadModal: React.FC<TransferUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [recipientId, setRecipientId] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileSha256, setFileSha256] = useState<string | null>(null);
  const [isHashing, setIsHashing] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setSelectedFile(null);
      setFileSha256(null);
      api
        .getUsers()
        .then((res) => {
          setUsers(res.items);
          if (res.items.length > 0) {
            setRecipientId(res.items[0].id);
          }
        })
        .catch(() => setError('Failed to load recipient directory.'));
    }
  }, [isOpen]);

  const handleFileChange = async (file: File) => {
    setSelectedFile(file);
    setError(null);
    setIsHashing(true);

    try {
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
      setFileSha256(hashHex);
    } catch {
      setFileSha256(null);
    } finally {
      setIsHashing(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !recipientId) return;

    setIsUploading(true);
    setError(null);

    try {
      await api.uploadTransfer(recipientId, selectedFile);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Upload and encryption pipeline failed.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-700/50 flex items-center justify-center text-cyan-400">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">
                Initiate Secure File Transfer
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                AES-256-GCM AEAD Ingestion Pipeline
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="flex items-center space-x-2 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Recipient Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
              DESTINATION RECIPIENT
            </label>
            <select
              value={recipientId}
              onChange={(e) => setRecipientId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.username} ({u.role}) — {u.branch || 'Branch Peer'}
                </option>
              ))}
            </select>
          </div>

          {/* File Dropzone */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
              PAYLOAD ATTACHMENT
            </label>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
                selectedFile
                  ? 'border-cyan-500/60 bg-cyan-950/10'
                  : 'border-slate-700 hover:border-slate-600 bg-slate-950/40'
              }`}
            >
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileChange(e.target.files[0]);
                  }
                }}
              />

              {selectedFile ? (
                <div className="flex flex-col items-center space-y-2">
                  <FileText className="w-8 h-8 text-cyan-400" />
                  <div>
                    <p className="text-xs font-medium text-slate-200">
                      {selectedFile.name}
                    </p>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                  <label
                    htmlFor="file-upload"
                    className="text-xs text-cyan-400 hover:underline cursor-pointer font-mono"
                  >
                    Change File
                  </label>
                </div>
              ) : (
                <div className="flex flex-col items-center space-y-2">
                  <Upload className="w-8 h-8 text-slate-500" />
                  <p className="text-xs text-slate-300">
                    Drag and drop file here, or{' '}
                    <label
                      htmlFor="file-upload"
                      className="text-cyan-400 hover:underline cursor-pointer font-medium"
                    >
                      browse
                    </label>
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono">
                    Max payload size: 50MB
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Cryptographic Inspector */}
          {selectedFile && (
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5 font-mono text-[11px]">
              <div className="flex items-center space-x-2 text-slate-300 font-semibold border-b border-slate-800 pb-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span>CRYPTOGRAPHIC PIPELINE PARAMETERS</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-400">
                <div>
                  <span className="text-slate-500">AEAD Cipher:</span> AES-256-GCM
                </div>
                <div>
                  <span className="text-slate-500">Tag Length:</span> 128-bit (16B)
                </div>
                <div>
                  <span className="text-slate-500">Nonce:</span> 96-bit CSPRNG
                </div>
                <div>
                  <span className="text-slate-500">Key Wrapping:</span> RFC 3394 KEK
                </div>
              </div>
              <div>
                <span className="text-slate-500 block mb-0.5">
                  Pre-Transfer SHA-256 Digest:
                </span>
                {isHashing ? (
                  <span className="text-amber-400 animate-pulse">
                    Computing cryptographic digest...
                  </span>
                ) : fileSha256 ? (
                  <span className="text-emerald-400 break-all select-all font-mono">
                    {fileSha256}
                  </span>
                ) : (
                  <span className="text-slate-500">Unavailable</span>
                )}
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors font-mono"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || isUploading || isHashing}
              className="flex items-center space-x-2 px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-mono"
            >
              {isUploading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Encrypting & Sending...</span>
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span>Encrypt & Send Payload</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
