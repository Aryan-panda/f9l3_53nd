export type UserRole = 'USER' | 'ADMIN';
export type UserStatus = 'ACTIVE' | 'SUSPENDED' | 'DISABLED';

export interface User {
  id: string;
  username: string;
  role: UserRole;
  status: UserStatus;
  branch?: string;
  created_at: string;
  last_login_at: string | null;
}

export type TransferState =
  | 'INITIALIZED'
  | 'UPLOADING'
  | 'UPLOADED'
  | 'ENCRYPTING'
  | 'ENCRYPTED'
  | 'TRANSFERRING'
  | 'RECEIVED'
  | 'DECRYPTING'
  | 'DECRYPTED'
  | 'INTEGRITY_CHECKING'
  | 'COMPLETED'
  | 'FAILED'
  | 'QUARANTINED'
  | 'REJECTED'
  | 'EXPIRED';

export interface Transfer {
  id: string;
  sender_id: string;
  recipient_id: string;
  filename: string;
  file_size: number;
  original_sha256: string;
  decrypted_sha256: string | null;
  state: TransferState;
  storage_path: string;
  quarantine_path: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  severity: 'INFO' | 'WARNING' | 'SECURITY_ALERT' | 'CRITICAL';
  actor_id: string | null;
  ip_address: string | null;
  target_resource: string | null;
  details: Record<string, unknown>;
  prev_record_hash: string;
  record_hash: string;
}

export interface AuditChainVerification {
  is_valid: boolean;
  total_records: number;
  broken_record_index: number | null;
  message: string;
}

export interface TunnelStatus {
  interface: string;
  status: string;
  local_ip: string;
  peer_ip: string;
  peer_endpoint: string | null;
  latest_handshake_seconds_ago: number | null;
  is_connected: boolean;
  mode: string;
}
