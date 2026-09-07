export interface User {
  id: string;
  email: string;
  full_name?: string;
  company_name?: string;
  role?: string;
  avatar_url?: string;
  auth_provider: 'local' | 'google';
  email_verified: boolean;
  is_active: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  message?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials {
  full_name: string;
  company_name?: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
  confirm_password: string;
}
