import { useState, useEffect } from 'react'
import { getAgents, updateAgent, createAgent, deleteAgent, getSettings, updateSettings } from '../api'
import { HelpIcon } from '../components/Tooltip'
import Modal from '../components/Modal'

interface Agent {
  id: string
  slug: string
  name: string
  system_prompt: string
  model: string
  temperature: number
  is_active: boolean
}

interface Model {
  id: string
  name: string
  description: string
}

export default function AgentManager() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [editedPrompt, setEditedPrompt] = useState('')
  const [editedModel, setEditedModel] = useState('')
  const [editedTemperature, setEditedTemperature] = useState(0.7)
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [defaultAgent, setDefaultAgent] = useState('misunderstanding_protector')
  const [newAgent, setNewAgent] = useState({
    slug: '',
    name: '',
    system_prompt: '',
    model: 'gpt-4-turbo-preview',
    temperature: 0.7
  })

  useEffect(() => {
    loadAgents()
    loadModels()
    loadSettings()
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

  const loadModels = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/api/playground/models`)
      const data = await response.json()
      setModels(data.models || [])
    } catch (error) {
      console.error('Failed to load models:', error)
      // Fallback models
      setModels([
        { id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo Preview', description: 'Default' },
        { id: 'gpt-4', name: 'GPT-4', description: 'Default' },
        { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Default' }
      ])
    }
  }

  const loadSettings = async () => {
    try {
      const settings = await getSettings()
      setDefaultAgent(settings.default_agent || 'misunderstanding_protector')
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  const handleSetDefault = async (slug: string) => {
    try {
      await updateSettings({ default_agent: slug })
      setDefaultAgent(slug)
    } catch (error) {
      console.error('Failed to update default agent:', error)
      alert('Failed to update default agent')
    }
  }

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent)
    setEditedPrompt(agent.system_prompt)
    setEditedModel(agent.model || 'gpt-4-turbo-preview')
    setEditedTemperature(agent.temperature || 0.7)
  }

  const handleSave = async () => {
    if (!selectedAgent) return

    setSaving(true)
    try {
      const updated = await updateAgent(selectedAgent.slug, {
        system_prompt: editedPrompt,
        model: editedModel,
        temperature: editedTemperature
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

  const handleCreate = async () => {
    try {
      const created = await createAgent(newAgent)
      await loadAgents()
      setSelectedAgent(created)
      setEditedPrompt(created.system_prompt)
      setEditedModel(created.model)
      setEditedTemperature(created.temperature)
      setShowCreateModal(false)
      setNewAgent({
        slug: '',
        name: '',
        system_prompt: '',
        model: 'gpt-4-turbo-preview',
        temperature: 0.7
      })
    } catch (error: any) {
      alert(`Failed to create agent: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDelete = async (slug: string) => {
    try {
      await deleteAgent(slug)
      await loadAgents()
      if (selectedAgent?.slug === slug) {
        setSelectedAgent(null)
        setEditedPrompt('')
      }
    } catch (error) {
      alert('Failed to delete agent')
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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Lista Agentów</h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              Nowy Agent
            </button>
          </div>
          {loading ? (
            <p className="text-gray-500">Ładowanie...</p>
          ) : agents.length === 0 ? (
            <p className="text-red-500">Brak agentów</p>
          ) : (
            <div className="space-y-2">
              {agents.map(agent => (
                <div key={agent.id} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="defaultAgent"
                    checked={defaultAgent === agent.slug}
                    onChange={() => handleSetDefault(agent.slug)}
                    className="mr-2"
                  />
                  <button
                    onClick={() => handleSelectAgent(agent)}
                    className={`flex-1 text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedAgent?.id === agent.id
                        ? 'bg-blue-100 text-blue-900'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{agent.name}</div>
                    <div className="text-sm text-gray-500">{agent.slug}</div>
                  </button>
                  <button
                    onClick={() => handleDelete(agent.slug)}
                    className="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                  >
                    Usuń
                  </button>
                </div>
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
              <div className="space-y-4">
                {/* Model Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    Model AI
                    <HelpIcon tooltip="Model który będzie używany przez tego agenta" />
                  </label>
                  <select
                    value={editedModel}
                    onChange={(e) => setEditedModel(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {models.map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name} - {model.description}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Temperature */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    Temperature: {editedTemperature}
                    <HelpIcon tooltip="0.0 = deterministyczne, 1.5 = bardzo kreatywne. Zalecane: 0.7" />
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1.5"
                    step="0.1"
                    value={editedTemperature}
                    onChange={(e) => setEditedTemperature(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0.0 (Precyzyjny)</span>
                    <span>0.7 (Zalecany)</span>
                    <span>1.5 (Kreatywny)</span>
                  </div>
                </div>

                {/* System Prompt */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                    System Prompt
                    <HelpIcon tooltip="Główne instrukcje określające zachowanie agenta w produkcji" />
                  </label>
                  <textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    className="w-full h-64 px-3 py-2 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="System prompt..."
                  />
                </div>
              </div>
            </>
          ) : (
            <p className="text-gray-500">Wybierz agenta do edycji</p>
          )}
        </div>
      </div>

      {/* Create Agent Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Nowy Agent"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nazwa
            </label>
            <input
              type="text"
              value={newAgent.name}
              onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="np. Pomocnik Emocjonalny"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Slug (unikalny identyfikator)
            </label>
            <input
              type="text"
              value={newAgent.slug}
              onChange={(e) => setNewAgent({ ...newAgent, slug: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="np. emotional_helper"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model AI
            </label>
            <select
              value={newAgent.model}
              onChange={(e) => setNewAgent({ ...newAgent, model: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {models.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {newAgent.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1.5"
              step="0.1"
              value={newAgent.temperature}
              onChange={(e) => setNewAgent({ ...newAgent, temperature: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Prompt
            </label>
            <textarea
              value={newAgent.system_prompt}
              onChange={(e) => setNewAgent({ ...newAgent, system_prompt: e.target.value })}
              className="w-full h-40 px-3 py-2 border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Instrukcje dla agenta..."
            />
          </div>

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Anuluj
            </button>
            <button
              onClick={handleCreate}
              disabled={!newAgent.name || !newAgent.slug || !newAgent.system_prompt}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Utwórz Agenta
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}