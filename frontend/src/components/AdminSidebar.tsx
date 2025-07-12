import { useState, useEffect } from 'react'
import { HelpIcon } from './Tooltip'

interface SidebarItem {
  id: string
  label: string
  icon: string
  tooltip: string
}

interface AdminSidebarProps {
  activeItem: string
  onItemClick: (id: string) => void
}

const menuItems: SidebarItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: '🏠',
    tooltip: 'Panel główny z metrykami (wkrótce)'
  },
  {
    id: 'agents',
    label: 'Agents',
    icon: '🤖',
    tooltip: 'Zarządzaj promptami agentów'
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    tooltip: 'Ustawienia systemowe'
  }
]

export default function AdminSidebar({ activeItem, onItemClick }: AdminSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    const saved = localStorage.getItem('adminSidebarExpanded')
    return saved !== 'false'
  })

  useEffect(() => {
    localStorage.setItem('adminSidebarExpanded', String(isExpanded))
  }, [isExpanded])

  return (
    <div className={`bg-white border-r border-gray-200 transition-all duration-300 flex flex-col ${
      isExpanded ? 'w-60' : 'w-16'
    }`}>
      {/* Toggle Button */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center text-gray-600 hover:text-gray-900 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d={isExpanded ? "M11 19l-7-7 7-7m8 14l-7-7 7-7" : "M13 5l7 7-7 7M5 5l7 7-7 7"}
            />
          </svg>
        </button>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => onItemClick(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              activeItem === item.id
                ? 'bg-blue-50 text-blue-700 border-blue-200 border'
                : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-xl flex-shrink-0">{item.icon}</span>
            {isExpanded && (
              <span className="text-sm font-medium">{item.label}</span>
            )}
            {!isExpanded && (
              <div className="absolute left-16 ml-2 invisible group-hover:visible">
                <HelpIcon tooltip={item.label} />
              </div>
            )}
          </button>
        ))}

        {/* Playground Link */}
        <div className="pt-4 mt-4 border-t border-gray-200">
          <button
            onClick={() => window.location.href = '/playground'}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <span className="text-xl flex-shrink-0">🧪</span>
            {isExpanded && (
              <>
                <span className="text-sm font-medium">Playground</span>
                <HelpIcon tooltip="Testuj prompty bez zapisywania" />
              </>
            )}
            {!isExpanded && (
              <div className="absolute left-16 ml-2 invisible group-hover:visible">
                <HelpIcon tooltip="Playground" />
              </div>
            )}
          </button>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        {isExpanded ? (
          <div className="text-xs text-gray-400">
            RELATRIX Admin v2.0
          </div>
        ) : (
          <div className="text-center text-xs text-gray-400">
            v2
          </div>
        )}
      </div>
    </div>
  )
}