import React from 'react'
import { Session, TestUser } from '../../../types/playground.types'
import { HelpIcon } from '../../Tooltip'

interface SessionsTabProps {
  sessions: Session[]
  testUsers: TestUser[]
  selectedUser: TestUser | null
  onUserSelect: (user: TestUser) => void
  onUserCreate: () => void
  onSessionSelect: (session: Session) => void
  onSessionDelete: (sessionId: string) => void
}

export const SessionsTab: React.FC<SessionsTabProps> = ({
  sessions,
  testUsers,
  selectedUser,
  onUserSelect,
  onUserCreate,
  onSessionSelect,
  onSessionDelete
}) => {
  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString('pl-PL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getMemoryBadgeColor = (type: string) => {
    switch (type) {
      case 'mem0':
        return 'bg-green-100 text-green-700'
      case 'zep':
        return 'bg-purple-100 text-purple-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="space-y-4">
      {/* Test Users */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="flex items-center text-sm font-medium text-gray-700">
            Test Users
            <HelpIcon tooltip="Użytkownicy testowi dla Mem0 i Zep" />
          </label>
          <button
            onClick={onUserCreate}
            className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            New User
          </button>
        </div>
        
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {testUsers.length === 0 ? (
            <p className="text-sm text-gray-500">No test users yet</p>
          ) : (
            testUsers.map(user => (
              <div
                key={user.id}
                onClick={() => onUserSelect(user)}
                className={`p-2 border rounded-lg cursor-pointer transition-colors ${
                  selectedUser?.id === user.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="font-medium text-sm">{user.name}</div>
                <div className="text-xs text-gray-500">
                  Created: {formatDate(user.created_at)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Sessions */}
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          Sessions
          <HelpIcon tooltip="Historia sesji dla wybranego użytkownika" />
        </label>
        
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500">
              {selectedUser ? 'No sessions for this user' : 'Select a user first'}
            </p>
          ) : (
            sessions.map(session => (
              <div
                key={session.id}
                className="p-2 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">
                        {session.title || 'Untitled Session'}
                      </span>
                      <span className={`px-1.5 py-0.5 text-xs rounded ${getMemoryBadgeColor(session.memory_type)}`}>
                        {session.memory_type}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(session.created_at)} • {session.message_count} messages
                    </div>
                  </div>
                  
                  <div className="flex gap-1 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onSessionSelect(session)
                      }}
                      className="p-1 hover:bg-gray-200 rounded"
                      title="Load session"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('Delete this session?')) {
                          onSessionDelete(session.id)
                        }
                      }}
                      className="p-1 hover:bg-red-100 rounded text-red-600"
                      title="Delete session"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}