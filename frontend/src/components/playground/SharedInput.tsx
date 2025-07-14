import React, { useState } from 'react'
import { HelpIcon } from '../Tooltip'

interface SharedInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
}

export const SharedInput: React.FC<SharedInputProps> = ({ 
  onSend, 
  disabled = false,
  placeholder = "Type your message..."
}) => {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim() || disabled) return
    onSend(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-white border-t p-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
        >
          Send to All
          <HelpIcon tooltip="Send message to all 3 chat windows (Enter)" />
        </button>
      </div>
    </div>
  )
}