import { Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import AuthPage from './pages/AuthPage'

export default function App() {
  return (
    <div className="h-screen flex flex-col">
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
        <Route path="/login" element={<AuthPage />} />
        <Route path="/register" element={<AuthPage />} />
      </Routes>
    </div>
  )
}
