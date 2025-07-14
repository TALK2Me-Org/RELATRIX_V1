import React from 'react'
import { Message as MessageType } from '../../../types/playground.types'

interface MessageProps {
  message: MessageType
  showJson?: boolean
}

export const Message: React.FC<MessageProps> = ({ message, showJson = true }) => {
  const highlightJSON = (content: string) => {
    if (!showJson) return content
    
    const jsonRegex = /\{"agent":\s*"[^"]+"\}/g
    const parts = content.split(jsonRegex)
    const matches = content.match(jsonRegex) || []
    
    return (
      <>
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {matches[i] && (
              <span className="bg-yellow-200 px-1 rounded font-mono text-sm">
                {matches[i]}
              </span>
            )}
          </span>
        ))}
      </>
    )
  }

  return (
    <div className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
      <div className={`inline-block max-w-[80%] p-3 rounded-lg ${
        message.role === 'user' 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-100 text-gray-800'
      }`}>
        <div className="whitespace-pre-wrap break-words">
          {message.role === 'assistant' && showJson ? (
            highlightJSON(message.content)
          ) : (
            message.content
          )}
        </div>
      </div>
    </div>
  )
}