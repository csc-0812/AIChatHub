/**
 * SSE (Server-Sent Events) 处理工具
 */

/**
 * 解析SSE事件数据
 */
export function parseSSEEvent(line) {
  if (line.startsWith('data: ')) {
    const data = line.slice(6)
    if (data === '[DONE]') {
      return { type: 'done' }
    }
    try {
      return { type: 'data', data: JSON.parse(data) }
    } catch (e) {
      return { type: 'text', data }
    }
  }
  return null
}

/**
 * 处理SSE流
 * @param {ReadableStream} reader - 响应体的reader
 * @param {Object} callbacks - 回调函数
 */
export async function handleSSEStream(reader, callbacks = {}) {
  const { onMessage, onError, onDone } = callbacks
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmedLine = line.trim()
        if (!trimmedLine) continue

        const event = parseSSEEvent(trimmedLine)
        if (!event) continue

        if (event.type === 'done') {
          onDone?.()
          return
        } else if (event.type === 'data') {
          if (event.data.error) {
            onError?.(event.data.error)
            return
          }
          onMessage?.(event.data)
        } else if (event.type === 'text') {
          onMessage?.({ content: event.data })
        }
      }
    }
  } catch (error) {
    onError?.(error.message)
  }
}
