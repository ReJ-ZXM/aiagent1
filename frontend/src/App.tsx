import { Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <div className="h-screen flex flex-col">
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
      </Routes>
    </div>
  )
}
