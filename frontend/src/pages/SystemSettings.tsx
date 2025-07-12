import { useState, useEffect } from 'react'
import { getSettings, updateSettings } from '../api'
import { HelpIcon } from '../components/Tooltip'

export default function SystemSettings() {
  const [enableFallback, setEnableFallback] = useState(true)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const settings = await getSettings()
      setEnableFallback(settings.enable_fallback ?? true)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateSettings({ enable_fallback: enableFallback })
      alert('Ustawienia zapisane!')
    } catch (error) {
      console.error('Failed to update settings:', error)
      alert('Błąd podczas zapisywania ustawień')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          Ustawienia Systemowe
          <HelpIcon tooltip="Globalne ustawienia wpływające na działanie całego systemu" />
        </h1>
        <p className="text-gray-600 mt-1">Konfiguruj zachowanie systemu RELATRIX</p>
      </div>

      {loading ? (
        <div className="text-gray-500">Ładowanie ustawień...</div>
      ) : (
        <div className="space-y-6">
          {/* Fallback Setting */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              Agent Switching
              <HelpIcon tooltip="Ustawienia związane z przełączaniem między agentami" />
            </h2>
            
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <label className="flex items-center gap-2 font-medium text-gray-900">
                    Enable Fallback Detection
                    <HelpIcon tooltip="Włącz/wyłącz automatyczne wykrywanie agenta przez GPT-3.5" />
                  </label>
                  <p className="text-sm text-gray-600 mt-1">
                    Gdy włączone, system użyje GPT-3.5 do wykrycia czy przełączyć agenta, 
                    jeśli obecny agent nie dodał JSON do odpowiedzi.
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    <strong>Zalety:</strong> Lepsze wykrywanie intencji użytkownika<br/>
                    <strong>Wady:</strong> Dodatkowe 1-2 sekundy opóźnienia, dodatkowy koszt
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={enableFallback}
                    onChange={(e) => setEnableFallback(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Status:</strong> {enableFallback ? 'Włączone' : 'Wyłączone'}
                </p>
                <p className="text-xs text-gray-500">
                  {enableFallback 
                    ? 'Agenci będą automatycznie przełączani nawet bez JSON w odpowiedzi'
                    : 'Agenci będą przełączani TYLKO gdy dodadzą JSON do odpowiedzi'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Future Settings */}
          <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-medium text-gray-700 mb-2">Przyszłe ustawienia</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Limity użycia API</li>
              <li>• Konfiguracja Mem0</li>
              <li>• Ustawienia bezpieczeństwa</li>
              <li>• Integracje zewnętrzne</li>
            </ul>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              {saving ? 'Zapisywanie...' : 'Zapisz ustawienia'}
              <HelpIcon tooltip="Zapisz wszystkie zmiany" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}