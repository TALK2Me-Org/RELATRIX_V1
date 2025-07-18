import React from 'react'
import { Agent, PlaygroundSettings } from '../../../types/playground.types'
import { HelpIcon } from '../../Tooltip'

interface SettingsTabProps {
  agents: Agent[]
  selectedAgent: Agent | null
  systemPrompt: string
  settings: PlaygroundSettings
  models: Array<{ id: string; name: string; description?: string }>
  onAgentChange: (slug: string) => void
  onSystemPromptChange: (prompt: string) => void
  onSettingsChange: (settings: PlaygroundSettings) => void
  onPromptModalOpen: () => void
}

export const SettingsTab: React.FC<SettingsTabProps> = ({
  agents,
  selectedAgent,
  systemPrompt,
  settings,
  models,
  onAgentChange,
  onSystemPromptChange,
  onSettingsChange,
  onPromptModalOpen
}) => {
  return (
    <div className="space-y-4">
      {/* Agent Selection */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
          Select Agent
          <HelpIcon tooltip="Wybierz którego agenta chcesz testować. Możesz edytować jego prompt bez wpływu na produkcję." />
        </label>
        <select
          value={selectedAgent?.slug || ''}
          onChange={(e) => onAgentChange(e.target.value)}
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
            onClick={onPromptModalOpen}
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
          onChange={(e) => onSystemPromptChange(e.target.value)}
          className="w-full h-32 px-3 py-2 border rounded-lg font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          onChange={(e) => onSettingsChange({ ...settings, model: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {models.map(model => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
      </div>

      {/* Temperature */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-1">
          Temperature: {settings.temperature}
          <HelpIcon tooltip="0 = deterministyczny, 1 = kreatywny. Dla testów zwykle 0.7" />
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={settings.temperature}
          onChange={(e) => onSettingsChange({ ...settings, temperature: parseFloat(e.target.value) })}
          className="w-full"
        />
      </div>

      {/* Options */}
      <div className="space-y-2">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={settings.show_json}
            onChange={(e) => onSettingsChange({ ...settings, show_json: e.target.checked })}
            className="rounded"
          />
          <span className="text-sm">Highlight JSON</span>
          <HelpIcon tooltip="Podświetl fragmenty JSON w odpowiedziach agentów" />
        </label>
        
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={settings.auto_switch}
            onChange={(e) => onSettingsChange({ ...settings, auto_switch: e.target.checked })}
            className="rounded"
          />
          <span className="text-sm">Auto Switch Agent</span>
          <HelpIcon tooltip="Automatycznie przełącz agenta gdy wykryje JSON" />
        </label>
      </div>
    </div>
  )
}