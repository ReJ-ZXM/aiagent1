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

  const handleVoiceResult = (transcript: string) => {
    if (transcript.trim()) {
      onSend(transcript.trim())
    }
  }

  return (
    <div className="border-t bg-white px-4 py-3 shrink-0">
      <div className="max-w-3xl mx-auto flex items-center gap-2">
        <VoiceButton onResult={handleVoiceResult} disabled={disabled} />

        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'AI 正在回复...' : '输入旅行需求，如"明天去杭州3天，预算5000"...'}
          disabled={disabled}
          className="flex-1 border rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-50 disabled:text-gray-400"
        />

        {disabled ? (
          <button
            onClick={onStop}
            className="bg-red-500 text-white rounded-full w-9 h-9 flex items-center justify-center hover:bg-red-600 transition shrink-0"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1" /></svg>
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!text.trim()}
            className="bg-blue-500 text-white rounded-full w-9 h-9 flex items-center justify-center hover:bg-blue-600 transition shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}
