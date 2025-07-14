// Playground Types

export interface Agent {
  slug: string
  name: string
  system_prompt: string
  model?: string
  temperature?: number
}

export interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
  raw_content?: string
  detected_json?: string
  debug_info?: any
}

export interface PlaygroundSettings {
  model: string
  temperature: number
  show_json: boolean
  enable_fallback: boolean
  auto_switch: boolean
}

export interface TokenUsage {
  input: number
  output: number
  total: number
  lastInput: number
  lastOutput: number
}

export interface Session {
  id: string
  user_id: string
  title: string
  created_at: number
  last_message_at?: number
  message_count: number
  memory_type: 'context' | 'mem0' | 'zep'
}

export interface TestUser {
  id: string
  name: string
  created_at: number
  last_used: number
}

export type MemoryMode = 'none' | 'mem0' | 'zep'
export type LeftPanelTab = 'settings' | 'sessions'
export type RightPanelTab = 'analysis' | 'raw' | 'clean'