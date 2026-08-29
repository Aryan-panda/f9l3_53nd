import React, { useState, useEffect } from 'react';
import { Users, UserX, UserCheck } from 'lucide-react';

import { api } from '../services/api';
import { User, UserStatus } from '../types';

export const UserManagementView: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionUserId, setActionUserId] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.getUsers();
      setUsers(res.items);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleStatusChange = async (userId: string, newStatus: UserStatus) => {
    setActionUserId(userId);
    try {
      await api.updateUserStatus(userId, newStatus);
      await fetchUsers();
    } catch {
      // Handle error
    } finally {
      setActionUserId(null);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <Users className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white font-mono">
            BRANCH IDENTITY & ACCESS CONTROL
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          Total Users: {users.length}
        </span>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-slate-400 font-mono">
          Loading branch users directory...
        </div>
      ) : (
        <div className="divide-y divide-slate-800 font-mono text-xs">
          {users.map((u) => {
            const isProcessing = actionUserId === u.id;
            return (
              <div
                key={u.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-950/40 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-semibold text-xs">
                    {u.username[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-200">
                        {u.username}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                        {u.role}
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                          u.status === 'ACTIVE'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : u.status === 'SUSPENDED'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-rose-950 text-rose-300 border border-rose-800'
                        }`}
                      >
                        {u.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      UUID: {u.id.slice(0, 12)}... • Branch: {u.branch || 'Branch A'} • Last
                      Login:{' '}
                      {u.last_login_at
                        ? new Date(u.last_login_at).toLocaleTimeString()
                        : 'Never'}
                    </p>
                  </div>
                </div>

                {/* Status Action Buttons */}
                <div className="flex items-center space-x-2 self-end sm:self-center">
                  {u.status !== 'ACTIVE' ? (
                    <button
                      onClick={() => handleStatusChange(u.id, 'ACTIVE')}
                      disabled={isProcessing}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-800 text-emerald-300 text-[11px] transition-colors"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>Activate</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStatusChange(u.id, 'SUSPENDED')}
                      disabled={isProcessing}
                      className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-amber-950/60 hover:bg-amber-900/80 border border-amber-800 text-amber-300 text-[11px] transition-colors"
                    >
                      <UserX className="w-3.5 h-3.5" />
                      <span>Suspend</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
