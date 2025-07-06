// Chat related types

export interface Agent {
  slug: string;
  name: string;
  description: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agentId?: string;
  timestamp: Date;
}

export interface StreamChunk {
  type: 'content' | 'transfer' | 'metadata' | 'error';
  content?: string;
  agent_id?: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface ChatSession {
  sessionId: string;
  currentAgent: Agent;
  messages: Message[];
}

export interface TransferEvent {
  from_agent: string;
  to_agent: string;
  reason: string;
  timestamp: string;
}