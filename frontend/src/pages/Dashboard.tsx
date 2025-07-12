import { HelpIcon } from '../components/Tooltip'

export default function Dashboard() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          Dashboard
          <HelpIcon tooltip="Panel główny z metrykami i statystykami systemu (w przygotowaniu)" />
        </h1>
        <p className="text-gray-600 mt-1">Przegląd działania systemu RELATRIX</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Placeholder Cards */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Aktywni użytkownicy</h3>
          <p className="text-3xl font-bold text-blue-600">-</p>
          <p className="text-sm text-gray-500 mt-2">Wkrótce dostępne</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Rozmowy dzisiaj</h3>
          <p className="text-3xl font-bold text-green-600">-</p>
          <p className="text-sm text-gray-500 mt-2">Wkrótce dostępne</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Zużycie tokenów</h3>
          <p className="text-3xl font-bold text-purple-600">-</p>
          <p className="text-sm text-gray-500 mt-2">Wkrótce dostępne</p>
        </div>
      </div>

      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Planowane funkcje</h2>
        <ul className="space-y-2 text-gray-600">
          <li className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>Metryki użycia w czasie rzeczywistym</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>Statystyki przełączeń między agentami</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>Monitoring kosztów API</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>Analiza najczęstszych problemów</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-green-500">✓</span>
            <span>Eksport raportów</span>
          </li>
        </ul>
      </div>
    </div>
  )
}