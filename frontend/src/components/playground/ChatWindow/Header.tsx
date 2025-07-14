import React from 'react'
import { TokenUsage } from '../../../types/playground.types'
import { HelpIcon } from '../../Tooltip'

interface HeaderProps {
  title: string
  tokens: TokenUsage
  onClear: () => void
  memoryBadge?: string
}

export const Header: React.FC<HeaderProps> = ({ title, tokens, onClear, memoryBadge }) => {
  return (
    <div className="bg-white border-b px-4 py-3 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-2">
        <h2 className="font-medium">{title}</h2>
        {memoryBadge && (
          <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
            {memoryBadge}
          </span>
        )}
      </div>
      
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500">
          In: {tokens.input} • Out: {tokens.output} • Total: {tokens.total}
        </span>
        
        <button
          onClick={onClear}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
          title="Clear messages"
        >
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  )
}