import React, { useRef, useEffect } from 'react'
import { Message } from './Message'
import { Message as MessageType } from '../../../types/playground.types'

interface MessageListProps {
  messages: MessageType[]
  streaming: string
  loading: boolean
  showJson?: boolean
}

export const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  streaming, 
  loading, 
  showJson = true 
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.map((msg, idx) => (
        <Message key={idx} message={msg} showJson={showJson} />
      ))}
      
      {streaming && (
        <Message 
          message={{ role: 'assistant', content: streaming }} 
          showJson={showJson} 
        />
      )}
      
      {loading && !streaming && (
        <div className="text-left mb-4">
          <div className="inline-block bg-gray-100 text-gray-800 p-3 rounded-lg">
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  )
}