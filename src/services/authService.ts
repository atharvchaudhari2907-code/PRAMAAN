import { User, AuthResponse, LoginCredentials, SignupCredentials, PasswordResetConfirm } from '../types/auth';

const API_BASE = '/api';

function extractErrorMessage(err: any, fallback: string, status?: number): string {
  if (status === 404) return 'Authentication endpoint not reachable. Please verify the backend server is running.';
  if (!err) return fallback;
  if (typeof err === 'string') return err;
  if (typeof err.detail === 'string') return err.detail;
  if (Array.isArray(err.detail) && err.detail.length > 0) {
    const first = err.detail[0];
    if (typeof first === 'string') return first;
    if (first && first.msg) return first.msg;
  }
  if (typeof err.message === 'string') return err.message;
  return fallback;
}

export const authService = {
  async register(credentials: SignupCredentials): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        email: credentials.email.trim().toLowerCase(),
        password: credentials.password,
        full_name: credentials.full_name.trim(),
        company_name: credentials.company_name?.trim() || undefined,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      throw new Error(extractErrorMessage(errData, 'Registration failed. Please check your details.', res.status));
    }

    const data: AuthResponse = await res.json();
    if (data.access_token) {
      localStorage.setItem('bis_access_token', data.access_token);
    }
    return data;
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        email: credentials.email.trim().toLowerCase(),
        password: credentials.password,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      throw new Error(extractErrorMessage(errData, 'Invalid email or password.', res.status));
    }

    const data: AuthResponse = await res.json();
    if (data.access_token) {
      localStorage.setItem('bis_access_token', data.access_token);
    }
    return data;
  },

  async getCurrentUser(): Promise<User | null> {
    const token = localStorage.getItem('bis_access_token');
    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers,
        credentials: 'include',
      });
      if (res.ok) {
        return await res.json();
      }
      if (res.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('bis_access_token');
      }
      return null;
    } catch {
      return null;
    }
  },

  async logout(): Promise<void> {
    const token = localStorage.getItem('bis_access_token');
    localStorage.removeItem('bis_access_token');
    try {
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers,
        credentials: 'include',
      });
    } catch {
      // Best-effort logout cleanup
    }
  },

  async verifyEmail(token: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/auth/verify-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ token }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(extractErrorMessage(err, 'This verification link is invalid or expired.'));
    }
    return await res.json();
  },

  async resendVerification(email: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/auth/resend-verification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(extractErrorMessage(err, 'Failed to resend verification link.'));
    }
    return await res.json();
  },

  async forgotPassword(email: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(extractErrorMessage(err, 'Failed to process password reset request.'));
    }
    return await res.json();
  },

  async resetPassword(data: PasswordResetConfirm): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(extractErrorMessage(err, 'This reset link is invalid or expired.'));
    }
    return await res.json();
  },
};
