import { useState, useCallback, useRef } from 'react'
import { Message, TokenUsage, MemoryMode } from '../../types/playground.types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface UsePlaygroundSSEProps {
  mode: MemoryMode
  sessionId?: string
  userId?: string
}

export function usePlaygroundSSE({ mode, sessionId, userId }: UsePlaygroundSSEProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState('')
  const [loading, setLoading] = useState(false)
  const [tokens, setTokens] = useState<TokenUsage>({ input: 0, output: 0, total: 0 })
  const eventSourceRef = useRef<EventSource | null>(null)

  const getEndpoint = useCallback(() => {
    switch (mode) {
      case 'mem0':
        return `${API_URL}/api/playground-mem0/sse`
      case 'zep':
        return `${API_URL}/api/playground-zep/sse`
      default:
        return `${API_URL}/api/playground/sse`
    }
  }, [mode])

  const sendMessage = useCallback(async (
    content: string,
    agentSlug: string,
    systemPrompt: string,
    model: string,
    temperature: number
  ) => {
    if (!content.trim() || loading) return

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: Date.now()
    }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)
    setStreaming('')

    // Close previous connection if exists
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    try {
      // Build params based on mode
      const params = new URLSearchParams({
        agent_slug: agentSlug,
        system_prompt: systemPrompt,
        message: content,
        model,
        temperature: temperature.toString()
      })

      // Add mode-specific params
      if (mode === 'mem0' && userId) {
        params.append('user_id', userId)
      } else if (mode === 'zep' && sessionId && userId) {
        params.append('session_id', sessionId)
        params.append('user_id', userId)
      } else if (mode === 'none') {
        // Add history for context mode
        const history = messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
        params.append('history', JSON.stringify(history))
      }

      const eventSource = new EventSource(`${getEndpoint()}?${params}`)
      eventSourceRef.current = eventSource

      let fullResponse = ''
      let detectedJson: string | null = null

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close()
          
          const assistantMessage: Message = {
            role: 'assistant',
            content: fullResponse,
            timestamp: Date.now(),
            detected_json: detectedJson || undefined
          }

          setMessages(prev => [...prev, assistantMessage])
          setStreaming('')
          setLoading(false)
          return
        }

        try {
          const data = JSON.parse(event.data)
          
          if (data.error) {
            throw new Error(data.error)
          }

          if (data.chunk) {
            fullResponse += data.chunk
            setStreaming(fullResponse)
          }

          if (data.detected_json) {
            detectedJson = data.detected_json
          }

          // Update tokens when received
          if (data.input_tokens !== undefined && data.output_tokens !== undefined) {
            setTokens({
              input: data.input_tokens,
              output: data.output_tokens,
              total: data.total_tokens
            })
          }
        } catch (e) {
          console.error(`[${mode}] Parse error:`, e)
        }
      }

      eventSource.onerror = (error) => {
        console.error(`[${mode}] SSE error:`, error)
        eventSource.close()
        
        const errorMessage: Message = {
          role: 'assistant',
          content: `Error: Connection failed for ${mode} mode`,
          timestamp: Date.now()
        }
        
        setMessages(prev => [...prev, errorMessage])
        setStreaming('')
        setLoading(false)
      }
    } catch (error) {
      console.error(`[${mode}] Error:`, error)
      setLoading(false)
    }
  }, [mode, messages, loading, getEndpoint, sessionId, userId])

  const clearMessages = useCallback(() => {
    setMessages([])
    setTokens({ input: 0, output: 0, total: 0 })
  }, [])

  return {
    messages,
    streaming,
    loading,
    tokens,
    sendMessage,
    clearMessages
  }
}