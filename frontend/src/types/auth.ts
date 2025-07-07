export interface User {
  id: string;
  email: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  metadata?: Record<string, any>;
}