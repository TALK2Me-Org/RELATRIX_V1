import { useState, useEffect } from 'react'
import { HelpIcon } from './components/Tooltip'
import { testPlayground } from './PlaygroundAPI'

interface Agent {
  slug: string
  name: string
  system_prompt: string
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

export default function Playground() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [systemPrompt, setSystemPrompt] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'analysis' | 'raw' | 'clean'>('analysis')
  const [currentDebug, setCurrentDebug] = useState<any>(null)
  
  const [settings, setSettings] = useState<PlaygroundSettings>({
    model: 'gpt-4',
    temperature: 0.7,
    show_json: true,
    enable_fallback: true
  })

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await fetch('/api/agents')
      const data = await response.json()
      setAgents(data)
      if (data.length > 0) {
        setSelectedAgent(data[0])
        setSystemPrompt(data[0].system_prompt)
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const handleAgentChange = (slug: string) => {
    const agent = agents.find(a => a.slug === slug)
    if (agent) {
      setSelectedAgent(agent)
      setSystemPrompt(agent.system_prompt)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !selectedAgent || loading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await testPlayground({
        agent_slug: selectedAgent.slug,
        system_prompt: systemPrompt,
        message: input,
        settings
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.clean_response,
        raw_content: response.raw_response,
        detected_json: response.detected_json,
        debug_info: response.debug_info
      }

      setMessages(prev => [...prev, assistantMessage])
      setCurrentDebug(response.debug_info)
    } catch (error) {
      console.error('Playground error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Failed to get response'
      }])
    } finally {
      setLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setCurrentDebug(null)
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-full px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">Agent Prompt Playground</h1>
            <HelpIcon tooltip="Testuj i debuguj prompty agentów bez zapisywania zmian" />
          </div>
          <button
            onClick={() => window.location.href = '/admin'}
            className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-1"
          >
            ← Back to Admin
            <HelpIcon tooltip="Wróć do panelu administracyjnego" />
          </button>
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
                <HelpIcon tooltip="Wybierz agenta do testowania. Zmiany promptu nie są zapisywane." />
              </label>
              <select
                value={selectedAgent?.slug || ''}
                onChange={(e) => handleAgentChange(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {agents.map(agent => (
                  <option key={agent.slug} value={agent.slug}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>

            {/* System Prompt */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                System Prompt
                <HelpIcon tooltip="Instrukcje systemowe dla agenta. Możesz edytować i testować różne wersje." />
              </label>
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
                <HelpIcon tooltip="Model AI do użycia. GPT-4 jest dokładniejszy, GPT-3.5 szybszy." />
              </label>
              <select
                value={settings.model}
                onChange={(e) => setSettings({...settings, model: e.target.value})}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
                Temperature: {settings.temperature}
                <HelpIcon tooltip="Kreatywność odpowiedzi. 0 = deterministyczne, 1 = kreatywne." />
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings({...settings, temperature: parseFloat(e.target.value)})}
                className="w-full"
              />
            </div>

            {/* Toggles */}
            <div className="space-y-2">
              <label className="flex items-center justify-between">
                <span className="flex items-center text-sm">
                  Show JSON Detection
                  <HelpIcon tooltip="Podświetla JSON w odpowiedziach agenta na żółto." />
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
                  <HelpIcon tooltip="Włącza automatyczne wykrywanie agenta gdy brak JSON." />
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
            <h2 className="font-medium">Test Conversation</h2>
            <button
              onClick={clearChat}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-1"
            >
              Clear Chat
              <HelpIcon tooltip="Wyczyść historię konwersacji testowej." />
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
                    <div>{highlightJSON(msg.raw_content || msg.content)}</div>
                  ) : (
                    <div>{msg.content}</div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
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
          </div>

          {/* Input */}
          <div className="bg-white border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
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
                <HelpIcon tooltip="Wyślij wiadomość testową do agenta" />
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
                <HelpIcon tooltip="Analiza odpowiedzi agenta i wykryte elementy." />
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
                <HelpIcon tooltip="Pełna odpowiedź z JSON przed czyszczeniem." />
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
                <HelpIcon tooltip="Odpowiedź pokazywana użytkownikowi (bez JSON)." />
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
                        <HelpIcon tooltip="JSON znaleziony w odpowiedzi" />
                      </h3>
                      <pre className="bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto">
                        {currentDebug.detected_json || 'None'}
                      </pre>
                    </div>
                    
                    <div>
                      <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Agent Switch
                        <HelpIcon tooltip="Czy agent zasugerował przełączenie" />
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
                        <HelpIcon tooltip="Liczba tokenów użytych w odpowiedzi" />
                      </h3>
                      <p className="text-sm">{currentDebug.token_count || 'N/A'}</p>
                    </div>

                    <div>
                      <h3 className="flex items-center text-sm font-medium text-gray-700 mb-1">
                        Processing Time
                        <HelpIcon tooltip="Czas generowania odpowiedzi" />
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
  )
}