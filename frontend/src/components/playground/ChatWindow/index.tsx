import React, { useEffect } from 'react'
import { Header } from './Header'
import { MessageList } from './MessageList'
import { usePlaygroundSSE } from '../../../hooks/playground/usePlaygroundSSE'
import { MemoryMode, Agent, PlaygroundSettings } from '../../../types/playground.types'

interface ChatWindowProps {
  title: string
  mode: MemoryMode
  agent: Agent | null
  systemPrompt: string
  settings: PlaygroundSettings
  sessionId?: string
  userId?: string
  onSendMessage?: (content: string) => void
  onAgentSwitch?: (agentSlug: string) => void
}

export const ChatWindow = React.forwardRef<
  { sendMessage: (content: string) => void },
  ChatWindowProps
>(({
  title,
  mode,
  agent,
  systemPrompt,
  settings,
  sessionId,
  userId,
  onSendMessage,
  onAgentSwitch
}, ref) => {
  const { messages, streaming, loading, tokens, sendMessage, clearMessages, detectedAgent } = usePlaygroundSSE({
    mode,
    sessionId,
    userId
  })

  // Handle auto-switch when agent is detected
  useEffect(() => {
    if (settings.auto_switch && detectedAgent && onAgentSwitch && detectedAgent !== agent?.slug) {
      onAgentSwitch(detectedAgent)
    }
  }, [detectedAgent, settings.auto_switch, onAgentSwitch, agent?.slug])

  const handleSend = (content: string) => {
    if (!agent) return
    
    sendMessage(
      content,
      agent.slug,
      systemPrompt,
      settings.model,
      settings.temperature
    )
    
    // Notify parent if needed
    if (onSendMessage) {
      onSendMessage(content)
    }
  }

  // Get memory badge
  const getMemoryBadge = () => {
    switch (mode) {
      case 'mem0':
        return 'Mem0'
      case 'zep':
        return 'Zep'
      default:
        return undefined
    }
  }

  // Expose sendMessage through ref
  React.useImperativeHandle(ref, () => ({
    sendMessage: handleSend
  }))

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white rounded-lg shadow-sm border">
      <Header 
        title={title}
        tokens={tokens}
        onClear={clearMessages}
        memoryBadge={getMemoryBadge()}
      />
      
      <MessageList
        messages={messages}
        streaming={streaming}
        loading={loading}
        showJson={settings.show_json}
      />
    </div>
  )
})

// Export a function to get chat instance methods
export const useChatWindow = () => {
  const sendMessageRef = React.useRef<(content: string) => void>()
  
  return {
    sendMessage: (content: string) => {
      if (sendMessageRef.current) {
        sendMessageRef.current(content)
      }
    },
    setSendMessageRef: (fn: (content: string) => void) => {
      sendMessageRef.current = fn
    }
  }
}