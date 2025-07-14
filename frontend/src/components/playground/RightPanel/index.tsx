import React from 'react'
import { useCollapsiblePanel } from '../../../hooks/playground/useCollapsiblePanel'
import { RightPanelTab, Message } from '../../../types/playground.types'
import { HelpIcon } from '../../Tooltip'

interface RightPanelProps {
  activeTab: RightPanelTab
  onTabChange: (tab: RightPanelTab) => void
  lastMessage: Message | null
}

export const RightPanel: React.FC<RightPanelProps> = ({ activeTab, onTabChange, lastMessage }) => {
  const panel = useCollapsiblePanel('playground_rightPanel')
  
  const renderTabContent = () => {
    if (!lastMessage || lastMessage.role !== 'assistant') {
      return <p className="text-gray-500 text-sm">No assistant response to analyze</p>
    }

    switch (activeTab) {
      case 'analysis':
        return (
          <div className="space-y-4">
            {lastMessage.detected_json && (
              <div>
                <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                  Detected JSON
                  <HelpIcon tooltip="JSON fragment detected for agent switching" />
                </h3>
                <pre className="bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto">
                  {lastMessage.detected_json}
                </pre>
              </div>
            )}
            
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-1">Response Stats</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Length:</span>
                  <span className="font-mono">{lastMessage.content.length} chars</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Words:</span>
                  <span className="font-mono">{lastMessage.content.split(/\s+/).length}</span>
                </div>
                {lastMessage.timestamp && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Time:</span>
                    <span className="font-mono">
                      {new Date(lastMessage.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {lastMessage.debug_info && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-1">Debug Info</h3>
                <pre className="bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto">
                  {JSON.stringify(lastMessage.debug_info, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )
        
      case 'raw':
        return (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Raw Response</h3>
            <pre className="bg-gray-100 p-3 rounded text-xs font-mono whitespace-pre-wrap break-words">
              {lastMessage.raw_content || lastMessage.content}
            </pre>
          </div>
        )
        
      case 'clean':
        return (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Clean Response</h3>
            <div className="bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap break-words">
              {lastMessage.content}
            </div>
          </div>
        )
        
      default:
        return null
    }
  }
  
  return (
    <div className={`bg-white border-l transition-all duration-300 flex flex-col ${
      panel.collapsed ? 'w-12' : 'w-96'
    }`}>
      {/* Toggle button */}
      <div className="flex justify-start p-2 border-b">
        <button
          onClick={panel.toggle}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
          title={panel.collapsed ? 'Expand panel' : 'Collapse panel'}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d={panel.collapsed ? 'M15 19l-7-7 7-7' : 'M9 5l7 7-7 7'}
            />
          </svg>
        </button>
      </div>
      
      {/* Content - hidden when collapsed */}
      <div className={panel.collapsed ? 'hidden' : 'flex flex-col flex-1 min-h-0'}>
        {/* Tabs */}
        <div className="border-b">
          <div className="flex">
            <button
              onClick={() => onTabChange('analysis')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'analysis' 
                  ? 'bg-gray-100 border-b-2 border-blue-600 text-blue-600' 
                  : 'hover:bg-gray-50'
              }`}
            >
              Analysis
            </button>
            <button
              onClick={() => onTabChange('raw')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'raw' 
                  ? 'bg-gray-100 border-b-2 border-blue-600 text-blue-600' 
                  : 'hover:bg-gray-50'
              }`}
            >
              Raw
            </button>
            <button
              onClick={() => onTabChange('clean')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'clean' 
                  ? 'bg-gray-100 border-b-2 border-blue-600 text-blue-600' 
                  : 'hover:bg-gray-50'
              }`}
            >
              Clean
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-4 overflow-y-auto">
          {renderTabContent()}
        </div>
      </div>
    </div>
  )
}