import { useCallback, useEffect, useState } from 'react'
import { useGameSocket } from './useGameSocket'

// Szkielet aplikacji (punkt 2). Kolejne punkty dodaja ekrany logowania,
// lobby i rozgrywki. Na razie pokazuje stan polaczenia z mostem.
export default function App() {
  const [lastType, setLastType] = useState(null)

  const onMessage = useCallback((msg) => {
    setLastType(msg.type)
  }, [])

  const { connected, connect } = useGameSocket(onMessage)

  useEffect(() => {
    connect()
  }, [connect])

  return (
    <div className="app">
      <h1>Statki</h1>
      <p>
        Most:{' '}
        <span className={connected ? 'ok' : 'bad'}>
          {connected ? 'połączono' : 'rozłączono'}
        </span>
      </p>
      {lastType && <p className="muted">Ostatni komunikat: {lastType}</p>}
    </div>
  )
}
