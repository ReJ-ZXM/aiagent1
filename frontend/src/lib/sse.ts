import { API_BASE } from '../config'

interface SSECallbacks {
  onThinking?: (msg: string) => void
  onToolCall?: (tool: string) => void
  onToolResult?: (tool: string, elapsed: number) => void
  onContent?: (delta: string) => void
  onCard?: (type: string, data: unknown) => void
  onDone?: (convId: string) => void
  onError?: (code: string, msg: string) => void
}

export function streamChat(
  content: string,
  conversationId: string | null,
  callbacks: SSECallbacks
): AbortController {
  const controller = new AbortController()

  const body = JSON.stringify({
    content,
    conversation_id: conversationId,
  })

  fetch(`${API_BASE}/api/v1/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError?.('HTTP_ERROR', `HTTP ${response.status}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const data = JSON.parse(dataStr)
              switch (currentEvent) {
                case 'thinking':
                  callbacks.onThinking?.(data.msg)
                  break
                case 'tool_call':
                  callbacks.onToolCall?.(data.tool)
                  break
                case 'tool_result':
                  callbacks.onToolResult?.(data.tool, data.elapsed_ms)
                  break
                case 'content':
                  callbacks.onContent?.(data.delta)
                  break
                case 'card':
                  callbacks.onCard?.(data.type, data.data)
                  break
                case 'done':
                  callbacks.onDone?.(data.conv_id)
                  break
                case 'error':
                  callbacks.onError?.(data.code, data.msg)
                  break
              }
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError?.('NETWORK_ERROR', err.message)
      }
    })

  return controller
}
