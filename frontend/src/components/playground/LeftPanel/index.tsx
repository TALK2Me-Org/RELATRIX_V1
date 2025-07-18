import React from 'react'
import { SettingsTab } from './SettingsTab'
import { SessionsTab } from './SessionsTab'
import { useCollapsiblePanel } from '../../../hooks/playground/useCollapsiblePanel'
import { LeftPanelTab, Agent, PlaygroundSettings, Session, TestUser } from '../../../types/playground.types'

interface LeftPanelProps {
  activeTab: LeftPanelTab
  onTabChange: (tab: LeftPanelTab) => void
  
  // Settings props
  agents: Agent[]
  selectedAgent: Agent | null
  systemPrompt: string
  settings: PlaygroundSettings
  models: Array<{ id: string; name: string; description?: string }>
  bedrockModels: Array<{ id: string; name: string; description?: string }>
  onAgentChange: (slug: string) => void
  onSystemPromptChange: (prompt: string) => void
  onSettingsChange: (settings: PlaygroundSettings) => void
  onPromptModalOpen: () => void
  
  // Sessions props
  sessions: Session[]
  testUsers: TestUser[]
  selectedUser: TestUser | null
  currentSessionId?: string | null
  onUserSelect: (user: TestUser) => void
  onUserCreate: () => void
  onUserUpdate: (userId: string, newName: string) => void
  onSessionSelect: (session: Session) => void
  onSessionDelete: (sessionId: string) => void
}

export const LeftPanel: React.FC<LeftPanelProps> = (props) => {
  const panel = useCollapsiblePanel('playground_leftPanel')
  
  return (
    <div className={`bg-white border-r transition-all duration-300 flex flex-col ${
      panel.collapsed ? 'w-12' : 'w-80'
    }`}>
      {/* Header with toggle */}
      <div className="flex items-center justify-between p-2 border-b">
        <h3 className={`font-medium ${panel.collapsed ? 'hidden' : ''}`}>Playground</h3>
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
              d={panel.collapsed ? 'M9 5l7 7-7 7' : 'M15 19l-7-7 7-7'}
            />
          </svg>
        </button>
      </div>
      
      {/* Tabs */}
      {!panel.collapsed && (
        <div className="flex border-b">
          <button
            onClick={() => props.onTabChange('settings')}
            className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
              props.activeTab === 'settings'
                ? 'bg-white border-b-2 border-blue-500 text-blue-600'
                : 'bg-gray-50 text-gray-600 hover:text-gray-800'
            }`}
          >
            Settings
          </button>
          <button
            onClick={() => props.onTabChange('sessions')}
            className={`flex-1 py-2 px-4 text-sm font-medium transition-colors ${
              props.activeTab === 'sessions'
                ? 'bg-white border-b-2 border-blue-500 text-blue-600'
                : 'bg-gray-50 text-gray-600 hover:text-gray-800'
            }`}
          >
            Sessions
          </button>
        </div>
      )}
      
      {/* Content */}
      <div className={`flex-1 overflow-y-auto p-4 ${panel.collapsed ? 'hidden' : ''}`}>
        {props.activeTab === 'settings' ? (
          <SettingsTab
            agents={props.agents}
            selectedAgent={props.selectedAgent}
            systemPrompt={props.systemPrompt}
            settings={props.settings}
            models={props.models}
            bedrockModels={props.bedrockModels}
            onAgentChange={props.onAgentChange}
            onSystemPromptChange={props.onSystemPromptChange}
            onSettingsChange={props.onSettingsChange}
            onPromptModalOpen={props.onPromptModalOpen}
          />
        ) : (
          <SessionsTab
            sessions={props.sessions}
            testUsers={props.testUsers}
            selectedUser={props.selectedUser}
            currentSessionId={props.currentSessionId}
            onUserSelect={props.onUserSelect}
            onUserCreate={props.onUserCreate}
            onUserUpdate={props.onUserUpdate}
            onSessionSelect={props.onSessionSelect}
            onSessionDelete={props.onSessionDelete}
          />
        )}
      </div>
    </div>
  )
}