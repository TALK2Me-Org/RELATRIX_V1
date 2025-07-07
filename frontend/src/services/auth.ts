import axios from 'axios';
import { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Token management
const TOKEN_KEY = 'relatrix_access_token';
const REFRESH_TOKEN_KEY = 'relatrix_refresh_token';

export const authService = {
  // Token management
  setTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  // API calls
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(`${API_URL}/api/auth/register`, data);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  },

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await axios.post<AuthResponse>(`${API_URL}/api/auth/login`, data);
    this.setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  },

  async logout(): Promise<void> {
    const token = this.getAccessToken();
    if (token) {
      try {
        await axios.post(`${API_URL}/api/auth/logout`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    this.clearTokens();
  },

  async getCurrentUser(): Promise<User | null> {
    const token = this.getAccessToken();
    if (!token) return null;

    try {
      const response = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data.user;
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  },

  async refreshToken(): Promise<AuthResponse | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await axios.post<AuthResponse>(`${API_URL}/api/auth/refresh`, {
        refresh_token: refreshToken
      });
      this.setTokens(response.data.access_token, response.data.refresh_token);
      return response.data;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearTokens();
      return null;
    }
  }
};

// Axios interceptor for adding auth header
axios.interceptors.request.use(
  (config) => {
    const token = authService.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Axios interceptor for handling 401 errors
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const newAuth = await authService.refreshToken();
      if (newAuth) {
        originalRequest.headers.Authorization = `Bearer ${newAuth.access_token}`;
        return axios(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);