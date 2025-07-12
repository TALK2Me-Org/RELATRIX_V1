import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { HelpIcon } from './components/Tooltip'
import Modal from './components/Modal'
import { getAgents } from './api'
import AdminSidebar from './components/AdminSidebar'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Agent {
  slug: string
  name: string
  system_prompt: string
  model?: string
  temperature?: number
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  raw_content?: string
  detected_json?: string
  debug_info?: any
}

interface PlaygroundSettings {
  model: string
  temperature: number
  show_json: boolean
  enable_fallback: boolean
  auto_switch: boolean
}

interface Model {
  id: string
  name: string
  description: string
}

interface TestUser {
  id: string
  name: string
  created_at: number
  last_used: number
  history: Message[]
}

// Chat Messages Component
const ChatMessages = ({ messages, streamingContent, loading, showJson }: {
  messages: Message[]
  streamingContent: string
  loading: boolean
  showJson: boolean
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])
  
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
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg, idx) => (
        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-2xl px-4 py-2 rounded-lg ${
            msg.role === 'user' 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-100 text-gray-900'
          }`}>
            {msg.role === 'assistant' && showJson ? (
              <div className="whitespace-pre-wrap">{highlightJSON(msg.raw_content || msg.content)}</div>
            ) : (
              <div className="whitespace-pre-wrap">{msg.content}</div>
            )}
          </div>
        </div>
      ))}
      {loading && streamingContent && (
        <div className="flex justify-start">
          <div className="bg-gray-100 px-4 py-2 rounded-lg text-gray-900 max-w-2xl">
            <div className="whitespace-pre-wrap">{streamingContent}</div>
          </div>
        </div>
      )}
      {loading && !streamingContent && (
        <div className="flex justify-start">
          <div className="bg-gray-100 px-4 py-2 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  )
}

export default function Playground() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [systemPrompt, setSystemPrompt] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'analysis' | 'raw' | 'clean'>('analysis')
  const [currentDebug, setCurrentDebug] = useState<any>(null)
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false)
  const [tempPrompt, setTempPrompt] = useState('')
  const [models, setModels] = useState<Model[]>([])
  const [totalTokens, setTotalTokens] = useState(0)
  const [streamingContent, setStreamingContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(() => {
    return localStorage.getItem('playground_leftPanel') === 'collapsed'
  })
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(() => {
    return localStorage.getItem('playground_rightPanel') === 'collapsed'
  })
  const [testUsers, setTestUsers] = useState<TestUser[]>([])
  const [selectedTestUser, setSelectedTestUser] = useState<TestUser | null>(null)
  const [showUserModal, setShowUserModal] = useState(false)
  const [splitView, setSplitView] = useState(false)
  const [mem0Messages, setMem0Messages] = useState<Message[]>([])
  const [mem0Streaming, setMem0Streaming] = useState('')
  const [mem0Loading, setMem0Loading] = useState(false)
  
  const [settings, setSettings] = useState<PlaygroundSettings>({
    model: 'gpt-4',
    temperature: 0.7,
    show_json: true,
    enable_fallback: true,
    auto_switch: false
  })

  useEffect(() => {
    loadAgents()
    loadModels()
    loadTestUsers()
  }, [])

  const loadAgents = async () => {
    try {
      const data = await getAgents()
      setAgents(data)
      
      if (data.length > 0) {
        setSelectedAgent(data[0])
        setSystemPrompt(data[0].system_prompt)
        // Also set model and temperature if available
        if (data[0].model) {
          setSettings(prev => ({...prev, model: data[0].model}))
        }
        if (data[0].temperature !== undefined) {
          setSettings(prev => ({...prev, temperature: data[0].temperature}))
        }
      }
    } catch (error) {
      console.error('[PLAYGROUND] Failed to load agents:', error)
      // Fallback to empty array to prevent undefined errors
      setAgents([])
    }
  }

  const loadModels = async () => {
    try {
      const response = await fetch(`${API_URL}/api/playground/models`)
      const data = await response.json()
      setModels(data.models || [])
    } catch (error) {
      console.error('Failed to load models:', error)
      // Fallback models
      setModels([
        { id: 'gpt-4', name: 'GPT-4', description: 'Default' },
        { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Default' }
      ])
    }
  }

  const handleAgentChange = (slug: string) => {
    const agent = agents.find(a => a.slug === slug)
    if (agent) {
      setSelectedAgent(agent)
      setSystemPrompt(agent.system_prompt)
      // Also update model and temperature if agent has them
      if (agent.model) {
        setSettings(prev => ({...prev, model: agent.model!}))
      }
      if (agent.temperature !== undefined) {
        setSettings(prev => ({...prev, temperature: agent.temperature!}))
      }
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  const toggleLeftPanel = () => {
    const newState = !leftPanelCollapsed
    setLeftPanelCollapsed(newState)
    localStorage.setItem('playground_leftPanel', newState ? 'collapsed' : 'expanded')
  }

  const toggleRightPanel = () => {
    const newState = !rightPanelCollapsed
    setRightPanelCollapsed(newState)
    localStorage.setItem('playground_rightPanel', newState ? 'collapsed' : 'expanded')
  }

  const loadTestUsers = () => {
    const saved = localStorage.getItem('playground_users')
    if (saved) {
      const users = JSON.parse(saved)
      setTestUsers(Object.values(users))
    }
  }

  const createTestUser = () => {
    const timestamp = Date.now()
    const random = Math.random().toString(36).substr(2, 5)
    const newUser: TestUser = {
      id: `playground_user_${timestamp}_${random}`,
      name: `Test User ${testUsers.length + 1}`,
      created_at: timestamp,
      last_used: timestamp,
      history: []
    }
    
    const allUsers = [...testUsers, newUser]
    setTestUsers(allUsers)
    setSelectedTestUser(newUser)
    
    // Save to localStorage
    const usersObj = allUsers.reduce((acc, user) => {
      acc[user.id] = user
      return acc
    }, {} as Record<string, TestUser>)
    localStorage.setItem('playground_users', JSON.stringify(usersObj))
    
    setShowUserModal(false)
  }

  const deleteTestUser = async (userId: string) => {
    if (!window.confirm('Delete this test user and all their data?')) return
    
    // Remove from state
    const remaining = testUsers.filter(u => u.id !== userId)
    setTestUsers(remaining)
    
    if (selectedTestUser?.id === userId) {
      setSelectedTestUser(null)
      setMessages([])
      setMem0Messages([])
    }
    
    // Save to localStorage
    const usersObj = remaining.reduce((acc, user) => {
      acc[user.id] = user
      return acc
    }, {} as Record<string, TestUser>)
    localStorage.setItem('playground_users', JSON.stringify(usersObj))
    
    // TODO: Call backend to delete from Mem0
  }

  const selectTestUser = (user: TestUser) => {
    setSelectedTestUser(user)
    setMessages(user.history || [])
    setMem0Messages([])
    setShowUserModal(false)
    
    // Update last_used
    user.last_used = Date.now()
    const allUsers = testUsers.map(u => u.id === user.id ? user : u)
    setTestUsers(allUsers)
    
    const usersObj = allUsers.reduce((acc, u) => {
      acc[u.id] = u
      return acc
    }, {} as Record<string, TestUser>)
    localStorage.setItem('playground_users', JSON.stringify(usersObj))
  }

  const handleSend = async () => {
    if (!input.trim() || !selectedAgent || loading) return
    
    // Check if we need test user for Mem0
    if (splitView && !selectedTestUser) {
      alert('Please select or create a test user for Mem0 comparison')
      return
    }

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    if (splitView) {
      setMem0Messages(prev => [...prev, userMessage])
    }
    setInput('')
    setLoading(true)
    setStreamingContent('')
    if (splitView) {
      setMem0Loading(true)
      setMem0Streaming('')
    }

    try {
      // Build history for context
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const params = new URLSearchParams({
        agent_slug: selectedAgent.slug,
        system_prompt: systemPrompt,
        message: input,
        history: JSON.stringify(history),
        model: settings.model,
        temperature: settings.temperature.toString()
      })

      const eventSource = new EventSource(`${API_URL}/api/playground/sse?${params}`)
      let fullResponse = ''
      let rawResponse = ''
      let detectedJson: string | null = null
      let agentSwitch: string | null = null
      let msgTokens = 0

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close()
          
          const assistantMessage: Message = {
            role: 'assistant',
            content: fullResponse,
            raw_content: rawResponse || fullResponse,
            detected_json: detectedJson || undefined,
            debug_info: {
              detected_json: detectedJson,
              agent_switch: agentSwitch,
              token_count: msgTokens,
              processing_time: 'streaming',
              model_used: settings.model,
              fallback_triggered: false
            }
          }

          setMessages(prev => [...prev, assistantMessage])
          setCurrentDebug(assistantMessage.debug_info)
          setStreamingContent('')
          setLoading(false)
          setTotalTokens(prev => prev + msgTokens)
          
          // Auto-switch agent if enabled and detected
          if (settings.auto_switch && agentSwitch && agentSwitch !== selectedAgent?.slug) {
            const newAgent = agents.find(a => a.slug === agentSwitch)
            if (newAgent) {
              handleAgentChange(agentSwitch)
            }
          }
          
          return
        }

        try {
          const data = JSON.parse(event.data)
          
          if (data.error) {
            throw new Error(data.error)
          }

          if (data.chunk) {
            fullResponse += data.chunk
            rawResponse += data.chunk
            setStreamingContent(fullResponse)
            msgTokens += data.tokens || 0
          }

          if (data.detected_json) {
            detectedJson = data.detected_json
            agentSwitch = data.agent_switch
          }

          if (data.total_tokens) {
            msgTokens = data.total_tokens
          }
        } catch (e) {
          console.error('Parse error:', e)
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE error:', error)
        eventSource.close()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Error: Connection failed'
        }])
        setStreamingContent('')
        setLoading(false)
      }
      
      // Start Mem0 stream if split view
      if (splitView && selectedTestUser) {
        startMem0Stream(input)
      }

    } catch (error) {
      console.error('Playground error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Failed to get response'
      }])
      setLoading(false)
    }
  }

  const startMem0Stream = async (message: string) => {
    if (!selectedAgent || !selectedTestUser) return
    
    try {
      const params = new URLSearchParams({
        agent_slug: selectedAgent.slug,
        system_prompt: systemPrompt,
        message: message,
        user_id: selectedTestUser.id,
        model: settings.model,
        temperature: settings.temperature.toString()
      })

      const eventSource = new EventSource(`${API_URL}/api/playground/mem0-sse?${params}`)
      let fullResponse = ''
      let detectedJson: string | null = null

      eventSource.onmessage = (event) => {
        if (event.data === '[DONE]') {
          eventSource.close()
          
          const assistantMessage: Message = {
            role: 'assistant',
            content: fullResponse,
            raw_content: fullResponse,
            detected_json: detectedJson || undefined
          }

          setMem0Messages(prev => [...prev, assistantMessage])
          setMem0Streaming('')
          setMem0Loading(false)
          
          // Save to test user history
          if (selectedTestUser) {
            selectedTestUser.history = [...messages, 
              { role: 'user', content: message },
              { role: 'assistant', content: fullResponse }
            ]
            const allUsers = testUsers.map(u => u.id === selectedTestUser.id ? selectedTestUser : u)
            const usersObj = allUsers.reduce((acc, u) => {
              acc[u.id] = u
              return acc
            }, {} as Record<string, TestUser>)
            localStorage.setItem('playground_users', JSON.stringify(usersObj))
          }
          
          return
        }

        try {
          const data = JSON.parse(event.data)
          
          if (data.error) {
            throw new Error(data.error)
          }

          if (data.chunk) {
            fullResponse += data.chunk
            setMem0Streaming(fullResponse)
          }

          if (data.detected_json) {
            detectedJson = data.detected_json
          }
        } catch (e) {
          console.error('Mem0 parse error:', e)
        }
      }

      eventSource.onerror = (error) => {
        console.error('Mem0 SSE error:', error)
        eventSource.close()
        setMem0Messages(prev => [...prev, {
          role: 'assistant',
          content: 'Error: Mem0 connection failed'
        }])
        setMem0Streaming('')
        setMem0Loading(false)
      }

    } catch (error) {
      console.error('Mem0 error:', error)
      setMem0Messages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Failed to get Mem0 response'
      }])
      setMem0Loading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setMem0Messages([])
    setCurrentDebug(null)
    setTotalTokens(0)
    setStreamingContent('')
    setMem0Streaming('')
  }


  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <AdminSidebar 
        activeItem="playground"
        onItemClick={(item) => {
          if (item === 'playground') return
          if (item === 'agents' || item === 'dashboard' || item === 'settings') {
            navigate('/admin')
          }
        }}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">Agent Prompt Playground</h1>
              <HelpIcon tooltip="Środowisko testowe do eksperymentowania z promptami. Zmiany nie są zapisywane w bazie danych." />
            </div>
            
            {/* Test User Controls */}
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={splitView}
                  onChange={(e) => setSplitView(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Split View (Mem0)</span>
                <HelpIcon tooltip="Porównaj odpowiedzi z i bez pamięci Mem0" />
              </label>
              
              {splitView && (
                <div className="flex items-center gap-2 border-l pl-3">
                  <span className="text-sm text-gray-600">
                    {selectedTestUser ? selectedTestUser.name : 'No user selected'}
                  </span>
                  <button
                    onClick={() => setShowUserModal(true)}
                    className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
                  >
                    Manage Users
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex h-[calc(100vh-60px)]">
        {/* Left Column - Configuration */}
        <div className={`bg-white border-r overflow-y-auto transition-all duration-300 ${
          leftPanelCollapsed ? 'w-12' : 'w-80'
        }`}>
          {/* Toggle button */}
          <div className="flex justify-end p-2 border-b">
            <button
              onClick={toggleLeftPanel}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              title={leftPanelCollapsed ? 'Expand panel' : 'Collapse panel'}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d={leftPanelCollapsed ? 'M9 5l7 7-7 7' : 'M15 19l-7-7 7-7'}
                />
              </svg>
            </button>
          </div>
          
          <div className={`p-4 space-y-4 ${leftPanelCollapsed ? 'hidden' : ''}`}>
            {/* Agent Selection */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Select Agent
                <HelpIcon tooltip="Wybierz którego agenta chcesz testować. Możesz edytować jego prompt bez wpływu na produkcję." />
              </label>
              <select
                value={selectedAgent?.slug || ''}
                onChange={(e) => handleAgentChange(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={agents.length === 0}
              >
                {agents.length === 0 ? (
                  <option value="">Loading agents...</option>
                ) : (
                  agents.map(agent => (
                    <option key={agent.slug} value={agent.slug}>
                      {agent.name}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* System Prompt */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="flex items-center text-sm font-medium text-gray-700">
                  System Prompt
                  <HelpIcon tooltip="Główne instrukcje określające zachowanie agenta. Edytuj i testuj różne wersje bez zapisywania." />
                </label>
                <button
                  onClick={() => {
                    setTempPrompt(systemPrompt)
                    setIsPromptModalOpen(true)
                  }}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                  Expand
                </button>
              </div>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="w-full h-64 px-3 py-2 border rounded-lg font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Model Selection */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Model
                <HelpIcon tooltip="GPT-4: najlepszy ale wolniejszy. GPT-3.5: szybszy i tańszy. Turbo: najnowsze wersje." />
              </label>
              <select
                value={settings.model}
                onChange={(e) => setSettings({...settings, model: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {models.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </select>
              {models.find(m => m.id === settings.model) && (
                <p className="mt-1 text-xs text-gray-500">
                  {models.find(m => m.id === settings.model)?.description}
                </p>
              )}
            </div>

            {/* Temperature */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Temperature: {settings.temperature}
                <HelpIcon tooltip="0.0 = przewidywalne, dokładne odpowiedzi. 1.0 = bardziej kreatywne i zróżnicowane. Zalecane: 0.7" />
              </label>
              <input
                type="range"
                min="0"
                max="1.5"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0.0</span>
                <span>0.7</span>
                <span>1.5</span>
              </div>
            </div>

            {/* Toggles */}
            <div className="space-y-2">
              <label className="flex items-center justify-between">
                <span className="flex items-center text-sm">
                  Show JSON Detection
                  <HelpIcon tooltip='Wizualnie zaznacza fragmenty JSON (np. {"agent": "nazwa"}) w odpowiedziach na żółto.' />
                </span>
                <input
                  type="checkbox"
                  checked={settings.show_json}
                  onChange={(e) => setSettings({...settings, show_json: e.target.checked})}
                  className="rounded"
                />
              </label>

              <label className="flex items-center justify-between">
                <span className="flex items-center text-sm">
                  Enable Fallback
                  <HelpIcon tooltip="Gdy agent nie doda JSON, system użyje GPT-3.5 do automatycznego wykrycia czy przełączyć agenta." />
                </span>
                <input
                  type="checkbox"
                  checked={settings.enable_fallback}
                  onChange={(e) => setSettings({...settings, enable_fallback: e.target.checked})}
                  className="rounded"
                />
              </label>

              <label className="flex items-center justify-between">
                <span className="flex items-center text-sm">
                  Auto-switch Agents
                  <HelpIcon tooltip="Automatycznie przełącza agenta gdy wykryje JSON w odpowiedzi" />
                </span>
                <input
                  type="checkbox"
                  checked={settings.auto_switch}
                  onChange={(e) => setSettings({...settings, auto_switch: e.target.checked})}
                  className="rounded"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Middle Column - Chat(s) */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 flex">
            {splitView ? (
              // Split view - two chats side by side
              <>
                {/* Left Chat - With Context */}
                <div className="flex-1 flex flex-col border-r min-h-0">
                  <div className="bg-white border-b px-4 py-3 flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center gap-2">
                      <h2 className="font-medium">With Context</h2>
                      <HelpIcon tooltip="Chat z pełną historią konwersacji" />
                    </div>
                  </div>
                  <ChatMessages 
                    messages={messages}
                    streamingContent={streamingContent}
                    loading={loading}
                    showJson={settings.show_json}
                  />
                </div>
                
                {/* Right Chat - With Mem0 */}
                <div className="flex-1 flex flex-col min-h-0">
                  <div className="bg-white border-b px-4 py-3 flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center gap-2">
                      <h2 className="font-medium">With Mem0</h2>
                      <HelpIcon tooltip="Chat używający pamięci Mem0" />
                    </div>
                  </div>
                  <ChatMessages 
                    messages={mem0Messages}
                    streamingContent={mem0Streaming}
                    loading={mem0Loading}
                    showJson={settings.show_json}
                  />
                </div>
              </>
            ) : (
              // Single chat view
              <div className="flex-1 flex flex-col min-h-0">
                <div className="bg-white border-b px-4 py-3 flex items-center justify-between flex-shrink-0">
                  <div className="flex items-center gap-4">
                    <h2 className="font-medium">Test Conversation</h2>
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <span>Total tokens:</span>
                      <span className="font-mono font-medium">{totalTokens}</span>
                      <HelpIcon tooltip="Przybliżona liczba tokenów zużytych w tej sesji" />
                    </div>
                  </div>
                  <button
                    onClick={clearChat}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-1"
                  >
                    Clear Chat
                    <HelpIcon tooltip="Usuń wszystkie wiadomości z bieżącej sesji testowej" />
                  </button>
                </div>
                <ChatMessages 
                  messages={messages}
                  streamingContent={streamingContent}
                  loading={loading}
                  showJson={settings.show_json}
                />
              </div>
            )}
          </div>
          
          {/* Input - shared for both views */}
          <div className="bg-white border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder={splitView && !selectedTestUser ? "Select a test user first..." : "Wpisz wiadomość testową..."}
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading || (splitView && !selectedTestUser)}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim() || (splitView && !selectedTestUser)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
              >
                Send
                <HelpIcon tooltip="Wyślij (Enter)" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Debug Info */}
        <div className={`bg-white border-l transition-all duration-300 ${
          rightPanelCollapsed ? 'w-12' : 'w-96'
        }`}>
          {/* Toggle button */}
          <div className="flex justify-start p-2 border-b">
            <button
              onClick={toggleRightPanel}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              title={rightPanelCollapsed ? 'Expand panel' : 'Collapse panel'}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d={rightPanelCollapsed ? 'M15 19l-7-7 7-7' : 'M9 5l7 7-7 7'}
                />
              </svg>
            </button>
          </div>
          
          {/* Content - hidden when collapsed */}
          <div className={rightPanelCollapsed ? 'hidden' : ''}>
            {/* Tabs */}
            <div className="border-b">
              <div className="flex">
              <button
                onClick={() => setActiveTab('analysis')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                  activeTab === 'analysis' 
                    ? 'bg-gray-100 border-b-2 border-blue-600 text-blue-600' 
                    : 'hover:bg-gray-50'
                }`}
              >
                Response Analysis
                <HelpIcon tooltip="Szczegółowa analiza: wykryty JSON, sugerowane przełączenie agenta, zużycie tokenów" />
              </button>
              <button
                onClick={() => setActiveTab('raw')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                  activeTab === 'raw' 
                    ? 'bg-gray-100 border-b-2 border-blue-600 text-blue-600' 
                    : 'hover:bg-gray-50'
                }`}
              >
                Raw Response
                <HelpIcon tooltip="Oryginalna odpowiedź agenta zawierająca wszystkie elementy JSON" />
              </button>
              <button
                onClick={() => setActiveTab('clean')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-1 ${
                  activeTab === 'clean' 
                    ? 'bg-gray-100 border-b-2 border-blue-600 text-blue-600' 
                    : 'hover:bg-gray-50'
                }`}
              >
                Clean Response
                <HelpIcon tooltip="Czysta odpowiedź bez elementów technicznych - to widzi użytkownik" />
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-4 overflow-y-auto h-[calc(100%-48px)]">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-sm">Rozpocznij konwersację aby zobaczyć analizę</p>
            ) : (
              <>
                {activeTab === 'analysis' && currentDebug && (
                  <div className="space-y-4">
                    <div>
                      <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Detected JSON
                        <HelpIcon tooltip="Fragment JSON wskazujący na przełączenie agenta" />
                      </h3>
                      <pre className="bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto">
                        {currentDebug.detected_json || 'None'}
                      </pre>
                    </div>
                    
                    <div>
                      <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Agent Switch
                        <HelpIcon tooltip="Nazwa agenta do którego system ma przełączyć" />
                      </h3>
                      <p className="text-sm">
                        {currentDebug.agent_switch ? 
                          `Yes → ${currentDebug.agent_switch}` : 
                          'No switch detected'
                        }
                      </p>
                    </div>

                    <div>
                      <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Token Count
                        <HelpIcon tooltip="Ilość tokenów zużytych na tę odpowiedź (wpływa na koszty)" />
                      </h3>
                      <p className="text-sm">{currentDebug.token_count || 'N/A'}</p>
                    </div>

                    <div>
                      <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Processing Time
                        <HelpIcon tooltip="Jak długo trwało wygenerowanie odpowiedzi" />
                      </h3>
                      <p className="text-sm">{currentDebug.processing_time || 'N/A'}</p>
                    </div>
                  </div>
                )}

                {activeTab === 'raw' && messages.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Last Assistant Response (Raw)</h3>
                    <pre className="bg-gray-100 p-3 rounded text-xs font-mono whitespace-pre-wrap">
                      {messages.filter(m => m.role === 'assistant').slice(-1)[0]?.raw_content || 
                       messages.filter(m => m.role === 'assistant').slice(-1)[0]?.content || 
                       'No assistant response yet'}
                    </pre>
                  </div>
                )}

                {activeTab === 'clean' && messages.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Last Assistant Response (Clean)</h3>
                    <pre className="bg-gray-100 p-3 rounded text-xs font-mono whitespace-pre-wrap">
                      {messages.filter(m => m.role === 'assistant').slice(-1)[0]?.content || 
                       'No assistant response yet'}
                    </pre>
                  </div>
                )}
              </>
            )}
          </div>
          </div>
        </div>
      </div>
      </div>

      {/* System Prompt Modal */}
      <Modal
        isOpen={isPromptModalOpen}
        onClose={() => setIsPromptModalOpen(false)}
        title="Edit System Prompt"
      >
        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            Edit the system prompt for <strong>{selectedAgent?.name}</strong>
          </div>
          <textarea
            value={tempPrompt}
            onChange={(e) => setTempPrompt(e.target.value)}
            className="w-full h-[60vh] px-4 py-3 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter system prompt..."
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={() => setIsPromptModalOpen(false)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                setSystemPrompt(tempPrompt)
                setIsPromptModalOpen(false)
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Save Changes
            </button>
          </div>
        </div>
      </Modal>
      
      {/* Test Users Modal */}
      <Modal
        isOpen={showUserModal}
        onClose={() => setShowUserModal(false)}
        title="Manage Test Users"
      >
        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            Create and manage test users for Mem0 testing
          </div>
          
          <button
            onClick={createTestUser}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create New Test User
          </button>
          
          <div className="border-t pt-4">
            <h3 className="font-medium mb-2">Existing Users</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {testUsers.length === 0 ? (
                <p className="text-sm text-gray-500">No test users yet</p>
              ) : (
                testUsers.map(user => (
                  <div key={user.id} className="flex items-center justify-between p-2 border rounded-lg">
                    <div>
                      <div className="font-medium">{user.name}</div>
                      <div className="text-xs text-gray-500">
                        Created: {new Date(user.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => selectTestUser(user)}
                        className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
                      >
                        Select
                      </button>
                      <button
                        onClick={() => deleteTestUser(user.id)}
                        className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}