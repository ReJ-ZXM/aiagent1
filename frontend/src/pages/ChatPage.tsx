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
      <header className="bg-white border-b px-4 py-3 flex items-center gap-4 shrink-0">
        <h1 className="text-lg font-bold">✈️ 旅行AI助手</h1>
        {thinking && (
          <span className="text-sm text-gray-500 animate-pulse truncate max-w-md">
            {thinking}
          </span>
        )}
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
