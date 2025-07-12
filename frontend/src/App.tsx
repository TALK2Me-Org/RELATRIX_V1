import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Chat from './Chat'
import Admin from './Admin'
import Auth from './auth'
import Playground from './Playground'
import { getStoredAuth } from './api'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const auth = getStoredAuth()
    if (auth) {
      setIsAuthenticated(true)
      setUser(auth)
    }
  }, [])

  const handleAuth = (authData: any) => {
    setIsAuthenticated(true)
    setUser(authData)
  }

  const handleLogout = () => {
    localStorage.removeItem('relatrix_token')
    localStorage.removeItem('relatrix_user')
    setIsAuthenticated(false)
    setUser(null)
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/auth" element={
            isAuthenticated ? 
              <Navigate to="/chat" /> : 
              <Auth onAuth={handleAuth} />
          } />
          <Route path="/chat" element={
            <Chat user={user} onLogout={handleLogout} />
          } />
          <Route path="/admin" element={
            isAuthenticated ? 
              <Admin user={user} onLogout={handleLogout} /> : 
              <Navigate to="/auth" />
          } />
          <Route path="/playground" element={<Playground />} />
          <Route path="/" element={<Navigate to="/chat" />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App