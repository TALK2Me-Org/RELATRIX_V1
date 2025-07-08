import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { streamChat } from './api'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
}

interface Props {
  user: any
  onLogout: () => void
}

const AGENTS = [
  { slug: 'misunderstanding_protector', name: 'Misunderstanding Protector' },
  { slug: 'emotional_vomit', name: 'Emotional Vomit' },
  { slug: 'solution_finder', name: 'Solution Finder' },
  { slug: 'conflict_solver', name: 'Conflict Solver' },
  { slug: 'communication_simulator', name: 'Communication Simulator' }
]

export default function Chat({ user, onLogout }: Props) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [currentAgent, setCurrentAgent] = useState('misunderstanding_protector')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      role: 'assistant',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, assistantMessage])

    try {
      await streamChat(
        input,
        currentAgent,
        (chunk) => {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1].content += chunk
            return updated
          })
        },
        (newAgent) => {
          if (newAgent && newAgent !== 'none') {
            setCurrentAgent(newAgent)
            const notification = `Switching to ${AGENTS.find(a => a.slug === newAgent)?.name}`
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1].content += `\n\n*${notification}*`
              return updated
            })
          }
        }
      )
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1].content = 'Error: Failed to get response'
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">RELATRIX</h1>
            <select 
              value={currentAgent} 
              onChange={(e) => setCurrentAgent(e.target.value)}
              className="px-3 py-1 border rounded-lg text-sm"
            >
              {AGENTS.map(agent => (
                <option key={agent.slug} value={agent.slug}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-4">
            {user && (
              <>
                <span className="text-sm text-gray-600">
                  {user.email}
                </span>
                <button
                  onClick={() => navigate('/admin')}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Admin
                </button>
              </>
            )}
            <button
              onClick={user ? onLogout : () => navigate('/auth')}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              {user ? 'Logout' : 'Login'}
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-4 ${
                message.role === 'user' ? 'text-right' : 'text-left'
              }`}
            >
              <div
                className={`inline-block px-4 py-2 rounded-lg max-w-2xl ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t bg-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              disabled={isStreaming}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSend}
              disabled={isStreaming || !input.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStreaming ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}