// API Service Layer
import axios from 'axios';
import { Agent, Message, StreamChunk } from '../types/chat';

// Use environment variable or default to production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://relatrix-backend.up.railway.app';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API endpoints
export const chatAPI = {
  // Get available agents
  getAgents: async (): Promise<{ agents: Agent[]; total: number }> => {
    const response = await api.get('/api/chat/agents');
    return response.data;
  },

  // Stream chat response
  streamChat: async (
    message: string, 
    onChunk: (chunk: StreamChunk) => void,
    sessionId?: string,
    onError?: (error: Error) => void
  ) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            try {
              const parsed = JSON.parse(data) as StreamChunk;
              onChunk(parsed);
            } catch (e) {
              console.error('Error parsing chunk:', e);
            }
          }
        }
      }
    } catch (error) {
      if (onError) {
        onError(error as Error);
      } else {
        console.error('Stream error:', error);
      }
    }
  },

  // Get session status
  getSessionStatus: async (sessionId: string) => {
    const response = await api.get(`/api/chat/session/${sessionId}`);
    return response.data;
  },

  // Transfer to another agent
  transferAgent: async (sessionId: string, targetAgent: string, reason?: string) => {
    const response = await api.post('/api/chat/transfer', {
      session_id: sessionId,
      target_agent: targetAgent,
      reason: reason || 'User requested transfer',
    });
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;