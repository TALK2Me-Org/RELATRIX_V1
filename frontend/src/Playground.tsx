import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { HelpIcon } from './components/Tooltip'
import Modal from './components/Modal'
import { testPlayground } from './PlaygroundAPI'
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
}

interface Model {
  id: string
  name: string
  description: string
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
  
  const [settings, setSettings] = useState<PlaygroundSettings>({
    model: 'gpt-4',
    temperature: 0.7,
    show_json: true,
    enable_fallback: true
  })

  useEffect(() => {
    loadAgents()
    loadModels()
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

  const handleSend = async () => {
    if (!input.trim() || !selectedAgent || loading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setStreamingContent('')

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

    } catch (error) {
      console.error('Playground error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Failed to get response'
      }])
      setLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setCurrentDebug(null)
    setTotalTokens(0)
  }

  const highlightJSON = (content: string) => {
    if (!settings.show_json) return content
    
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
          </div>
        </div>

        <div className="flex h-[calc(100vh-60px)]">
        {/* Left Column - Configuration */}
        <div className="w-80 bg-white border-r p-4 overflow-y-auto">
          <div className="space-y-4">
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
            </div>
          </div>
        </div>

        {/* Middle Column - Chat */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
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

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-2xl px-4 py-2 rounded-lg ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  {msg.role === 'assistant' && settings.show_json ? (
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

          {/* Input */}
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
                placeholder="Wpisz wiadomość testową..."
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
              >
                Send
                <HelpIcon tooltip="Wyślij (Enter)" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Debug Info */}
        <div className="w-96 bg-white border-l">
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
      </div>
    </div>
  )
}