import { useCallback, useEffect, useRef, useState } from 'react'
import { GATEWAY_URL } from './config'

/**
 * Hook zarzadzajacy polaczeniem WebSocket z mostem.
 * onMessage jest wywolywane dla kazdej wiadomosci protokolu (obiekt JSON).
 * Wiadomosc { type: '__DISCONNECTED__' } sygnalizuje rozlaczenie.
 */
export function useGameSocket(onMessage) {
  const wsRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connect = useCallback(() => {
    const existing = wsRef.current
    if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
      return
    }
    const ws = new WebSocket(GATEWAY_URL)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      onMessageRef.current?.({ type: '__DISCONNECTED__' })
    }
    ws.onerror = () => {}
    ws.onmessage = (event) => {
      let msg
      try {
        msg = JSON.parse(event.data)
      } catch {
        return
      }
      onMessageRef.current?.(msg)
    }
  }, [])

  const send = useCallback((type, fields = {}) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, ...fields }))
      return true
    }
    return false
  }, [])

  const close = useCallback(() => {
    wsRef.current?.close()
  }, [])

  useEffect(() => () => wsRef.current?.close(), [])

  return { connected, connect, send, close }
}
