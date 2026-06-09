import { useCallback, useEffect, useRef, useState } from 'react'
import { useGameSocket } from './useGameSocket'
import { sha256Hex } from './crypto'
import Login from './Login'

// Fazy aplikacji: login -> lobby -> game. Kolejne punkty rozwijaja lobby i gre.
export default function App() {
  const [phase, setPhase] = useState('login')
  const [username, setUsername] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const tokenRef = useRef(null)

  const onMessage = useCallback((msg) => {
    switch (msg.type) {
      case 'WELCOME':
        break
      case 'AUTH_OK':
        tokenRef.current = msg.token || null
        setBusy(false)
        setError(null)
        setPhase('lobby')
        break
      case 'AUTH_FAIL':
        setBusy(false)
        setError(msg.reason || 'Logowanie odrzucone.')
        break
      case 'ERROR':
        setBusy(false)
        setError(msg.message || msg.code)
        break
      case '__DISCONNECTED__':
        setError('Utracono połączenie z mostem.')
        setPhase('login')
        break
      default:
        break
    }
  }, [])

  const { connected, connect, send } = useGameSocket(onMessage)

  useEffect(() => {
    connect()
  }, [connect])

  useEffect(() => {
    if (connected) send('HELLO', { client_version: '1.0.0' })
  }, [connected, send])

  const handleLogin = useCallback(
    async (user, password) => {
      setBusy(true)
      setError(null)
      setUsername(user)
      const hash = await sha256Hex(password)
      send('AUTH', { username: user, password_hash: hash })
    },
    [send],
  )

  return (
    <div className="app">
      <h1>STATKI</h1>
      {phase === 'login' && (
        <Login onSubmit={handleLogin} error={error} busy={busy} connected={connected} />
      )}
      {phase === 'lobby' && (
        <div className="card">
          <h2>Witaj, {username}!</h2>
          <p className="muted">Zalogowano. Lobby pojawi się w kolejnym kroku.</p>
        </div>
      )}
    </div>
  )
}
