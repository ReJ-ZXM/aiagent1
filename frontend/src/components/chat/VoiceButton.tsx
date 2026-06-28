import { useState, useRef, useCallback } from 'react'

interface Props {
  onResult: (transcript: string) => void
  disabled: boolean
}

export default function VoiceButton({ onResult, disabled }: Props) {
  const [recording, setRecording] = useState(false)
  const [supported] = useState(
    () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  )
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        chunksRef.current = []

        // P0: Use browser Web Speech API for local recognition
        const SpeechRecognition =
          (window as Record<string, unknown>).SpeechRecognition ||
          (window as Record<string, unknown>).webkitSpeechRecognition
        if (SpeechRecognition) {
          const recognition = new (SpeechRecognition as new () => SpeechRecognition)()
          recognition.lang = 'zh-CN'
          recognition.interimResults = false
          recognition.onresult = (event: SpeechRecognitionEvent) => {
            const transcript = event.results[0][0].transcript
            onResult(transcript)
          }
          recognition.onerror = () => {
            onResult('')
          }
          recognition.start()
        } else {
          console.warn('浏览器不支持语音识别')
          onResult('')
        }
      }

      mediaRecorder.start()
      setRecording(true)
    } catch {
      console.warn('无法访问麦克风')
    }
  }, [onResult])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setRecording(false)
  }, [])

  if (!supported) return null

  return (
    <button
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onMouseLeave={stopRecording}
      onTouchStart={startRecording}
      onTouchEnd={stopRecording}
      disabled={disabled}
      className={`rounded-full w-9 h-9 flex items-center justify-center transition shrink-0 ${
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
