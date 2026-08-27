export type UserRole = 'ADMIN' | 'USER';

export type UserStatus = 'ACTIVE' | 'SUSPENDED' | 'DISABLED';

export type TransferState =
  | 'CREATED'
  | 'VALIDATING'
  | 'HASHING'
  | 'ENCRYPTING'
  | 'READY'
  | 'TRANSFERRING'
  | 'RECEIVED'
  | 'AUTHENTICATING'
  | 'DECRYPTING'
  | 'VERIFYING'
  | 'COMPLETED'
  | 'FAILED'
  | 'QUARANTINED'
  | 'REJECTED'
  | 'REPLAY_DETECTED';

export interface HealthStatus {
  status: string;
  app: string;
  environment?: string;
  storage?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
