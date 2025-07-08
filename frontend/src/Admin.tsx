import { useState, useEffect } from 'react'
import { getAgents, updateAgent } from './api'

interface Agent {
  id: string
  slug: string
  name: string
  system_prompt: string
  is_active: boolean
}

interface Props {
  user: any
  onLogout: () => void
}

export default function Admin({ user, onLogout }: Props) {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [editedPrompt, setEditedPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    setLoading(true)
    try {
      const data = await getAgents()
      setAgents(data)
      console.log('[ADMIN] Loaded agents:', data)
    } catch (error: any) {
      console.error('[ADMIN] Failed to load agents:', error)
      console.error('[ADMIN] Error details:', error.response?.data)
      alert(`Failed to load agents: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent)
    setEditedPrompt(agent.system_prompt)
  }

  const handleSave = async () => {
    if (!selectedAgent) return

    setSaving(true)
    try {
      const updated = await updateAgent(selectedAgent.slug, {
        system_prompt: editedPrompt
      })
      
      setAgents(prev => prev.map(a => 
        a.slug === updated.slug ? updated : a
      ))
      setSelectedAgent(updated)
      alert('Agent updated successfully!')
    } catch (error) {
      console.error('Failed to update agent:', error)
      alert('Failed to update agent')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-semibold">RELATRIX Admin</h1>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-500">
              API: {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
            </span>
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={onLogout}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Agent List */}
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold mb-4">Agents</h2>
            {loading ? (
              <p className="text-gray-500">Loading agents...</p>
            ) : agents.length === 0 ? (
              <p className="text-red-500">No agents found. Check backend connection.</p>
            ) : (
              <div className="space-y-2">
                {agents.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => handleSelectAgent(agent)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedAgent?.id === agent.id
                        ? 'bg-blue-100 text-blue-900'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{agent.name}</div>
                    <div className="text-sm text-gray-500">{agent.slug}</div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Editor */}
          <div className="md:col-span-2 bg-white rounded-lg shadow p-4">
            {selectedAgent ? (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">{selectedAgent.name}</h2>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                </div>
                <textarea
                  value={editedPrompt}
                  onChange={(e) => setEditedPrompt(e.target.value)}
                  className="w-full h-96 px-3 py-2 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="System prompt..."
                />
              </>
            ) : (
              <p className="text-gray-500">Select an agent to edit</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}