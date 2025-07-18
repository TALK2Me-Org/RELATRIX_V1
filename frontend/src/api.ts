import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Auth storage
export const getStoredAuth = () => {
  const token = localStorage.getItem('relatrix_token')
  const user = localStorage.getItem('relatrix_user')
  if (token && user) {
    return JSON.parse(user)
  }
  return null
}

// API client
const api = axios.create({
  baseURL: API_URL
})

// Add auth header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('relatrix_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth endpoints
export const register = async (email: string, password: string) => {
  const response = await api.post('/api/auth/register', { email, password })
  localStorage.setItem('relatrix_token', response.data.access_token)
  localStorage.setItem('relatrix_user', JSON.stringify({
    id: response.data.user_id,
    email: response.data.email
  }))
  return response.data
}

export const login = async (email: string, password: string) => {
  const response = await api.post('/api/auth/login', { email, password })
  localStorage.setItem('relatrix_token', response.data.access_token)
  localStorage.setItem('relatrix_user', JSON.stringify({
    id: response.data.user_id,
    email: response.data.email
  }))
  return response.data
}

export const logout = async () => {
  await api.post('/api/auth/logout')
  localStorage.removeItem('relatrix_token')
  localStorage.removeItem('relatrix_user')
}

// Agent endpoints
export const getAgents = async () => {
  const response = await api.get('/api/agents/')
  return response.data
}

export const updateAgent = async (slug: string, data: any) => {
  const response = await api.put(`/api/agents/${slug}`, data)
  return response.data
}

export const createAgent = async (data: {
  slug: string
  name: string
  system_prompt: string
  model: string
  temperature: number
}) => {
  const response = await api.post('/api/agents/', data)
  return response.data
}

export const deleteAgent = async (slug: string) => {
  const response = await api.delete(`/api/agents/${slug}`)
  return response.data
}

// Settings endpoints
export const getSettings = async () => {
  const response = await api.get('/api/settings')
  return response.data
}

export const updateSettings = async (settings: any) => {
  const response = await api.post('/api/settings', settings)
  return response.data
}

// Chat SSE streaming
export const streamChat = async (
  message: string,
  agentSlug: string,
  onChunk: (chunk: string) => void,
  onSwitch: (newAgent: string | null) => void
) => {
  const token = localStorage.getItem('relatrix_token')
  
  const params = new URLSearchParams({
    message,
    agent_slug: agentSlug
  })
  
  // Add token to query params for SSE (EventSource doesn't support headers)
  if (token) {
    params.append('token', token)
  }

  const eventSource = new EventSource(
    `${API_URL}/api/chat/sse?${params}`,
    { withCredentials: true }
  )

  return new Promise((resolve, reject) => {
    eventSource.onmessage = (event) => {
      console.log('[SSE] Received:', event.data)
      
      if (event.data === '[DONE]') {
        console.log('[SSE] Stream complete, closing connection')
        eventSource.close()
        resolve(void 0)
        return
      }

      try {
        const data = JSON.parse(event.data)
        
        if (data.error) {
          eventSource.close()
          reject(new Error(data.error))
          return
        }

        if (data.chunk) {
          onChunk(data.chunk)
        }

        if (data.switch) {
          console.log('[SSE] Agent switch:', data.switch)
          onSwitch(data.switch === 'none' ? null : data.switch)
        }
      } catch (e) {
        console.error('Parse error:', e)
      }
    }

    eventSource.onerror = (error) => {
      console.error('[SSE] Connection error:', error)
      eventSource.close()
      reject(error)
    }
    
    // Add timeout to prevent hanging
    const timeout = setTimeout(() => {
      console.error('[SSE] Timeout - closing connection')
      eventSource.close()
      reject(new Error('Stream timeout'))
    }, 30000) // 30 seconds timeout
    
    // Clear timeout on successful completion
    eventSource.addEventListener('close', () => {
      clearTimeout(timeout)
    })
  })
}