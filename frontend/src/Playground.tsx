import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAgents } from './api'
import AdminSidebar from './components/AdminSidebar'
import Modal from './components/Modal'

// Playground components
import { LeftPanel } from './components/playground/LeftPanel'
import { ChatWindow } from './components/playground/ChatWindow'
import { RightPanel } from './components/playground/RightPanel'
import { SharedInput } from './components/playground/SharedInput'

// Types
import { 
  Agent, 
  PlaygroundSettings, 
  LeftPanelTab, 
  RightPanelTab,
  Session,
  TestUser,
  Message,
  Model,
  ModelsResponse
} from './types/playground.types'

// API configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Playground() {
  const navigate = useNavigate()
  
  // Core state
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [systemPrompt, setSystemPrompt] = useState('')
  const [settings, setSettings] = useState<PlaygroundSettings>({
    model: 'gpt-4',
    temperature: 0.7,
    show_json: true,
    enable_fallback: true,
    auto_switch: false
  })
  const [models, setModels] = useState<Model[]>([])
  
  // UI state
  const [leftPanelTab, setLeftPanelTab] = useState<LeftPanelTab>('settings')
  const [rightPanelTab, setRightPanelTab] = useState<RightPanelTab>('analysis')
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false)
  const [tempPrompt, setTempPrompt] = useState('')
  
  // Session management
  const [sessions, setSessions] = useState<Session[]>([])
  const [testUsers, setTestUsers] = useState<TestUser[]>([])
  const [selectedUser, setSelectedUser] = useState<TestUser | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  
  // Chat refs for sending messages
  const contextChatRef = useRef<{ sendMessage: (content: string) => void }>()
  const mem0ChatRef = useRef<{ sendMessage: (content: string) => void }>()
  const zepChatRef = useRef<{ sendMessage: (content: string) => void }>()
  const bedrockChatRef = useRef<{ sendMessage: (content: string) => void }>()
  
  // Track last assistant message for debug panel
  const [lastAssistantMessage, setLastAssistantMessage] = useState<Message | null>(null)
  
  // Load initial data
  useEffect(() => {
    loadAgents()
    loadTestUsers()
    loadModels()
  }, [])
  
  // Load sessions when user changes
  useEffect(() => {
    if (selectedUser) {
      loadUserSessions(selectedUser.id)
    }
  }, [selectedUser])
  
  const loadAgents = async () => {
    try {
      const data = await getAgents()
      setAgents(data)
      
      if (data.length > 0 && !selectedAgent) {
        setSelectedAgent(data[0])
        setSystemPrompt(data[0].system_prompt)
        if (data[0].model) setSettings(prev => ({ ...prev, model: data[0].model! }))
        if (data[0].temperature !== undefined) setSettings(prev => ({ ...prev, temperature: data[0].temperature! }))
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }
  
  const loadModels = async () => {
    try {
      const response = await fetch(`${API_URL}/api/models`)
      const data: ModelsResponse = await response.json()
      // Set OpenAI models as default for the model picker
      setModels(data.openai)
    } catch (error) {
      console.error('Failed to load models:', error)
      // Fallback models
      setModels([
        { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
        { id: 'gpt-4', name: 'GPT-4' },
        { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' }
      ])
    }
  }
  
  const loadTestUsers = () => {
    const saved = localStorage.getItem('playground_users')
    if (saved) {
      const users = JSON.parse(saved)
      setTestUsers(Object.values(users))
    }
  }
  
  const loadUserSessions = async (userId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/playground-zep/sessions?user_id=${userId}`)
      if (response.ok) {
        const zepSessions = await response.json()
        
        // Convert to our Session format
        const formattedSessions: Session[] = zepSessions.map((s: any) => ({
          id: s.session_id || s.id,
          user_id: userId,
          title: s.title || `Session ${new Date(s.created_at).toLocaleDateString()}`,
          created_at: new Date(s.created_at).getTime(),
          last_message_at: s.last_message_at ? new Date(s.last_message_at).getTime() : undefined,
          message_count: s.message_count || 0,
          memory_type: 'zep' as const
        }))
        
        setSessions(formattedSessions)
      }
    } catch (error) {
      console.error('Failed to load Zep sessions:', error)
      setSessions([])
    }
  }
  
  const handleAgentChange = (slug: string) => {
    const agent = agents.find(a => a.slug === slug)
    if (agent) {
      setSelectedAgent(agent)
      setSystemPrompt(agent.system_prompt)
      if (agent.model) setSettings(prev => ({ ...prev, model: agent.model! }))
      if (agent.temperature !== undefined) setSettings(prev => ({ ...prev, temperature: agent.temperature! }))
    }
  }
  
  const handleSendToAll = (content: string) => {
    // Send to all 4 chat windows
    contextChatRef.current?.sendMessage(content)
    mem0ChatRef.current?.sendMessage(content)
    zepChatRef.current?.sendMessage(content)
    bedrockChatRef.current?.sendMessage(content)
  }
  
  const createTestUser = () => {
    const timestamp = Date.now()
    const newUser: TestUser = {
      id: `playground_user_${timestamp}`,
      name: `Test User ${testUsers.length + 1}`,
      created_at: timestamp,
      last_used: timestamp
    }
    
    const allUsers = [...testUsers, newUser]
    setTestUsers(allUsers)
    setSelectedUser(newUser)
    
    // Save to localStorage
    const usersObj = allUsers.reduce((acc, u) => {
      acc[u.id] = u
      return acc
    }, {} as Record<string, TestUser>)
    localStorage.setItem('playground_users', JSON.stringify(usersObj))
  }
  
  const createNewSession = () => {
    if (!selectedUser) return
    
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`
    setSessionId(newSessionId)
    return newSessionId
  }
  
  const handlePromptSave = () => {
    setSystemPrompt(tempPrompt)
    setIsPromptModalOpen(false)
  }
  
  const handleChatMessage = (message: Message) => {
    if (message.role === 'assistant') {
      setLastAssistantMessage(message)
    }
  }
  
  return (
    <div className="flex h-screen bg-gray-50">
      <AdminSidebar activeItem="playground" onItemClick={(id) => {
        // Custom navigation for playground
        switch(id) {
          case 'dashboard':
            navigate('/')  // Main app dashboard
            break
          case 'agents':
            navigate('/admin')  // Admin panel for agents
            break
          case 'settings':
            navigate('/admin')  // Admin panel for settings
            break
          default:
            // Do nothing for unknown items
            break
        }
      }} />
      
      <div className="flex-1 flex">
        {/* Left Panel */}
        <LeftPanel
          activeTab={leftPanelTab}
          onTabChange={setLeftPanelTab}
          agents={agents}
          selectedAgent={selectedAgent}
          systemPrompt={systemPrompt}
          settings={settings}
          models={models}
          onAgentChange={handleAgentChange}
          onSystemPromptChange={setSystemPrompt}
          onSettingsChange={setSettings}
          onPromptModalOpen={() => {
            setTempPrompt(systemPrompt)
            setIsPromptModalOpen(true)
          }}
          sessions={sessions}
          testUsers={testUsers}
          selectedUser={selectedUser}
          currentSessionId={sessionId}
          onUserSelect={setSelectedUser}
          onUserCreate={createTestUser}
          onSessionSelect={(session) => {
            setSessionId(session.id)
            // Load session messages into appropriate chat
          }}
          onSessionDelete={(id) => {
            setSessions(prev => prev.filter(s => s.id !== id))
          }}
        />
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Windows */}
          <div className="flex-1 grid grid-cols-4 gap-4 p-4 min-h-0 overflow-hidden">
            <ChatWindow
              title="FullContext"
              mode="none"
              agent={selectedAgent}
              systemPrompt={systemPrompt}
              settings={settings}
              ref={(ref) => { if (ref) contextChatRef.current = ref }}
              onSendMessage={(content) => handleChatMessage({ role: 'assistant', content })}
              onAgentSwitch={handleAgentChange}
            />
            
            <ChatWindow
              title="With Mem0"
              mode="mem0"
              agent={selectedAgent}
              systemPrompt={systemPrompt}
              settings={settings}
              userId={selectedUser?.id}
              ref={(ref) => { if (ref) mem0ChatRef.current = ref }}
              onSendMessage={(content) => handleChatMessage({ role: 'assistant', content })}
              onAgentSwitch={handleAgentChange}
            />
            
            <ChatWindow
              title="With Zep"
              mode="zep"
              agent={selectedAgent}
              systemPrompt={systemPrompt}
              settings={settings}
              sessionId={sessionId || createNewSession()}
              userId={selectedUser?.id}
              ref={(ref) => { if (ref) zepChatRef.current = ref }}
              onSendMessage={(content) => handleChatMessage({ role: 'assistant', content })}
              onAgentSwitch={handleAgentChange}
            />
            
            <ChatWindow
              title="AWS Bedrock"
              mode="bedrock"
              agent={selectedAgent}
              systemPrompt={systemPrompt}
              settings={settings}
              userId={selectedUser?.id}
              ref={(ref) => { if (ref) bedrockChatRef.current = ref }}
              onSendMessage={(content) => handleChatMessage({ role: 'assistant', content })}
              onAgentSwitch={handleAgentChange}
            />
          </div>
          
          {/* Shared Input */}
          <SharedInput
            onSend={handleSendToAll}
            disabled={!selectedAgent}
            placeholder={
              !selectedAgent 
                ? "Select an agent first..." 
                : (!selectedUser && (leftPanelTab === 'sessions'))
                  ? "Select or create a test user for memory modes..."
                  : "Type your test message..."
            }
          />
        </div>
        
        {/* Right Panel */}
        <RightPanel
          activeTab={rightPanelTab}
          onTabChange={setRightPanelTab}
          lastMessage={lastAssistantMessage}
        />
      </div>
      
      {/* Prompt Modal */}
      <Modal
        isOpen={isPromptModalOpen}
        onClose={() => setIsPromptModalOpen(false)}
        title="Edit System Prompt"
      >
        <div className="space-y-4">
          <textarea
            value={tempPrompt}
            onChange={(e) => setTempPrompt(e.target.value)}
            className="w-full h-96 px-3 py-2 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsPromptModalOpen(false)}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handlePromptSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Save
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}