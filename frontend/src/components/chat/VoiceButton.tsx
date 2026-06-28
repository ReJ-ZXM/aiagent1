import { useState, useRef, useCallback } from 'react'

interface Props {
  onResult: (transcript: string) => void
  disabled: boolean
}

// Web Speech API 没有 TS 类型定义，全部使用 any
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getSpeechRecognition(): any {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const w = window as any
  return w.SpeechRecognition || w.webkitSpeechRecognition || null
}

export default function VoiceButton({ onResult, disabled }: Props) {
  const [recording, setRecording] = useState(false)
  const [supported] = useState(() => getSpeechRecognition() !== null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null)

  const startRecording = useCallback(() => {
    const SpeechRecognition = getSpeechRecognition()
    if (!SpeechRecognition) {
      console.warn('浏览器不支持语音识别')
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.lang = 'zh-CN'
      recognition.interimResults = true
      recognition.continuous = true

      let finalTranscript = ''

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        let interim = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i]
          if (result.isFinal) {
            finalTranscript += result[0]?.transcript || ''
          } else {
            interim += result[0]?.transcript || ''
          }
        }
        if (interim) {
          console.log('🎤:', interim)
        }
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onerror = (event: any) => {
        console.warn('语音错误:', event.error)
        if (event.error === 'no-speech') {
          onResult('')
        }
        if (event.error !== 'aborted') {
          setRecording(false)
        }
      }

      recognition.onend = () => {
        setRecording(false)
        if (finalTranscript.trim()) {
          onResult(finalTranscript.trim())
        }
        recognitionRef.current = null
      }

      recognition.start()
      recognitionRef.current = recognition
      setRecording(true)
    } catch (e) {
      console.warn('无法启动语音识别:', e)
      setRecording(false)
    }
  }, [onResult])

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {
        // 可能已经停止了
      }
    }
  }, [])

  if (!supported) return null

  return (
    <button
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onMouseLeave={(e) => {
        // 只有正在录音时才在鼠标离开时停止
        if (recording && e.buttons === 0) {
          stopRecording()
        }
      }}
      onTouchStart={startRecording}
      onTouchEnd={stopRecording}
      disabled={disabled}
      className={`rounded-full w-9 h-9 flex items-center justify-center transition shrink-0 select-none ${
        recording
          ? 'bg-red-500 text-white animate-pulse scale-110'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
      } disabled:opacity-40 disabled:cursor-not-allowed`}
      title="按住说话"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    </button>
  )
}
