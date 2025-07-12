import { useState } from 'react'
import AdminSidebar from './components/AdminSidebar'
import Dashboard from './pages/Dashboard'
import AgentManager from './pages/AgentManager'
import SystemSettings from './pages/SystemSettings'

interface Props {
  user: any
  onLogout: () => void
}

export default function AdminNew({ user, onLogout }: Props) {
  const [activeSection, setActiveSection] = useState('agents')

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <Dashboard />
      case 'agents':
        return <AgentManager />
      case 'settings':
        return <SystemSettings />
      default:
        return <AgentManager />
    }
  }

  const handlePlayground = () => {
    window.location.href = '/playground'
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <AdminSidebar 
        activeItem={activeSection}
        onItemClick={setActiveSection}
        onPlayground={handlePlayground}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="px-6 py-3 flex items-center justify-between">
            <h1 className="text-xl font-semibold">RELATRIX Admin</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={onLogout}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}