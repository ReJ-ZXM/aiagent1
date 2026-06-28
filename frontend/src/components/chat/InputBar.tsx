import { useState, KeyboardEvent } from 'react'
import VoiceButton from './VoiceButton'

interface Props {
  onSend: (content: string) => void
  onStop: () => void
  disabled: boolean
}

export default function InputBar({ onSend, onStop, disabled }: Props) {
  const [text, setText] = useState('')

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t bg-white/90 backdrop-blur px-4 py-3 shrink-0">
      <div className="max-w-3xl mx-auto flex items-center gap-2">
        <VoiceButton onResult={(t) => t.trim() && onSend(t.trim())} disabled={disabled} />

        <div className="flex-1 relative">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'AI 正在回复...' : '输入旅行需求，如"明天去杭州3天，预算5000"...'}
            disabled={disabled}
            className="w-full border border-gray-200 rounded-full pl-4 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-travel-300 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-400 transition-shadow bg-white"
          />
        </div>

        {disabled ? (
          <button
            onClick={onStop}
            className="btn-icon bg-red-500 text-white hover:bg-red-600 shadow-md"
            title="停止生成"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!text.trim()}
            className="btn-icon bg-gradient-to-br from-travel-500 to-ocean-500 text-white shadow-md hover:shadow-lg disabled:opacity-30 disabled:shadow-none"
            title="发送"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}
