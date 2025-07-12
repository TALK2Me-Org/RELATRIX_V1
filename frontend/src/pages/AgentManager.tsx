import { useState, useEffect } from 'react'
import { getAgents, updateAgent } from '../api'
import { HelpIcon } from '../components/Tooltip'

interface Agent {
  id: string
  slug: string
  name: string
  system_prompt: string
  is_active: boolean
}

export default function AgentManager() {
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
      if (data.length > 0 && !selectedAgent) {
        setSelectedAgent(data[0])
        setEditedPrompt(data[0].system_prompt)
      }
    } catch (error: any) {
      console.error('[AGENTS] Failed to load agents:', error)
      alert(`Failed to load agents: ${error.message}`)
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
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          Agent Prompts
          <HelpIcon tooltip="Zarządzaj promptami systemowymi agentów. Zmiany są zapisywane w bazie danych." />
        </h1>
        <p className="text-gray-600 mt-1">Edytuj prompty systemowe dla każdego agenta</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Agent List */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Lista Agentów</h2>
          {loading ? (
            <p className="text-gray-500">Ładowanie...</p>
          ) : agents.length === 0 ? (
            <p className="text-red-500">Brak agentów</p>
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
                <div>
                  <h2 className="text-lg font-semibold">{selectedAgent.name}</h2>
                  <p className="text-sm text-gray-500">Slug: {selectedAgent.slug}</p>
                </div>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {saving ? 'Zapisywanie...' : 'Zapisz zmiany'}
                  <HelpIcon tooltip="Zapisz zmiany w bazie danych" />
                </button>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                  System Prompt
                  <HelpIcon tooltip="Główne instrukcje określające zachowanie agenta w produkcji" />
                </label>
                <textarea
                  value={editedPrompt}
                  onChange={(e) => setEditedPrompt(e.target.value)}
                  className="w-full h-96 px-3 py-2 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="System prompt..."
                />
              </div>
            </>
          ) : (
            <p className="text-gray-500">Wybierz agenta do edycji</p>
          )}
        </div>
      </div>
    </div>
  )
}