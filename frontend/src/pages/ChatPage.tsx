import { useState, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import MessageList from '../components/chat/MessageList'
import InputBar from '../components/chat/InputBar'
import { streamChat } from '../lib/sse'
import type { Message, SSECardData } from '../types'

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [thinking, setThinking] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [convId, setConvId] = useState<string | null>(conversationId || null)
  const abortRef = useRef<AbortController | null>(null)

  const handleSend = useCallback((content: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      content_type: 'text',
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsStreaming(true)
    setThinking('思考中...')

    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      content_type: 'text',
      cards: [],
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, assistantMsg])

    abortRef.current = streamChat(content, convId, {
      onThinking: (msg) => setThinking(msg),
      onToolCall: (tool) => setThinking(`正在调用: ${tool}...`),
      onContent: (delta) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: last.content + delta }
          }
          return updated
        })
      },
      onCard: (type, data) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last && last.role === 'assistant') {
            const existing = last.cards || []
            const cardData: SSECardData = { type: type as 'itinerary', data: data as SSECardData['data'] }
            updated[updated.length - 1] = { ...last, cards: [...existing, cardData] }
          }
          return updated
        })
      },
      onDone: (id) => {
        setConvId(id)
        setIsStreaming(false)
        setThinking('')
      },
      onError: (_code, msg) => {
        setThinking(`错误: ${msg}`)
        setIsStreaming(false)
      },
    })
  }, [convId])

  const handleStop = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
    setThinking('')
  }, [])

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-white/95 backdrop-blur border-b border-gray-100 px-4 py-3 flex items-center gap-3 shrink-0 shadow-sm">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-travel-500 to-ocean-500 flex items-center justify-center text-white shadow-md">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-bold text-gray-800">旅行 AI 助手</h1>
          {thinking && (
            <p className="text-xs text-travel-500 animate-pulse-soft truncate">{thinking}</p>
          )}
        </div>
        <button
          onClick={() => {
            setMessages([])
            setConvId(null)
            setThinking('')
          }}
          className="text-xs text-gray-400 hover:text-gray-600 transition px-3 py-1.5 rounded-lg hover:bg-gray-50"
          title="新对话"
        >
          + 新对话
        </button>
      </header>

      <MessageList messages={messages} />

      <InputBar
        onSend={handleSend}
        onStop={handleStop}
        disabled={isStreaming}
      />
    </div>
  )
}
