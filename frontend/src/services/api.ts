import {
  AuditChainVerification,
  AuditEvent,
  Transfer,
  TunnelStatus,
  User,
  UserStatus,
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = new Headers(options.headers || {});

    if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Enforce HttpOnly cookie handling
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      let errorData: { error?: { message?: string; code?: string } } = {};
      try {
        errorData = await response.json();
      } catch {
        // Fallback for non-JSON error bodies
      }
      const message =
        errorData?.error?.message ||
        `HTTP Error ${response.status}: ${response.statusText}`;
      throw new Error(message);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json() as Promise<T>;
  }

  // Auth & Session
  async login(username: string, password: string): Promise<{ user: User; message: string }> {
    return this.request<{ user: User; message: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async logout(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // User Management
  async getUsers(offset = 0, limit = 50): Promise<{ items: User[]; total: number }> {
    return this.request<{ items: User[]; total: number }>(
      `/users?offset=${offset}&limit=${limit}`
    );
  }

  async updateUserStatus(userId: string, status: UserStatus): Promise<User> {
    return this.request<User>(`/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // Transfers
  async getTransfers(
    offset = 0,
    limit = 50
  ): Promise<{ items: Transfer[]; total: number }> {
    return this.request<{ items: Transfer[]; total: number }>(
      `/transfers?offset=${offset}&limit=${limit}`
    );
  }

  async getTransfer(transferId: string): Promise<Transfer> {
    return this.request<Transfer>(`/transfers/${transferId}`);
  }

  async uploadTransfer(recipientId: string, file: File): Promise<Transfer> {
    const formData = new FormData();
    formData.append('recipient_id', recipientId);
    formData.append('file', file);

    return this.request<Transfer>('/transfers', {
      method: 'POST',
      body: formData,
    });
  }

  async downloadTransfer(transferId: string, filename: string): Promise<void> {
    const url = `${API_BASE}/transfers/${transferId}/download`;
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      let errorData: { error?: { message?: string } } = {};
      try {
        errorData = await response.json();
      } catch {
        // Fallback
      }
      throw new Error(
        errorData?.error?.message ||
          `Download failed with HTTP ${response.status}`
      );
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Admin & Audit
  async getAuditEvents(
    params: {
      offset?: number;
      limit?: number;
      eventType?: string;
      severity?: string;
    } = {}
  ): Promise<{ items: AuditEvent[]; total: number }> {
    const query = new URLSearchParams();
    if (params.offset !== undefined) query.set('offset', params.offset.toString());
    if (params.limit !== undefined) query.set('limit', params.limit.toString());
    if (params.eventType) query.set('event_type', params.eventType);
    if (params.severity) query.set('severity', params.severity);

    return this.request<{ items: AuditEvent[]; total: number }>(
      `/admin/audit-events?${query.toString()}`
    );
  }

  async verifyAuditChain(): Promise<AuditChainVerification> {
    return this.request<AuditChainVerification>('/admin/audit-events/verify', {
      method: 'POST',
    });
  }

  async getNetworkStatus(): Promise<TunnelStatus> {
    return this.request<TunnelStatus>('/admin/network/status');
  }
}

export const api = new ApiClient();
