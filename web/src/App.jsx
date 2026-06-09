import { useCallback, useEffect, useRef, useState } from 'react'
import { useGameSocket } from './useGameSocket'
import { sha256Hex } from './crypto'
import { emptyBoard, withCell } from './boards'
import Login from './Login'
import Lobby from './Lobby'
import Placement from './Placement'
import Game from './Game'

const HIT_MARKS = new Set(['HIT', 'SUNK'])
const DEFAULT_FLEET = [4, 3, 3, 3, 2]

// Fazy aplikacji: login -> lobby -> game.
export default function App() {
  const [phase, setPhase] = useState('login')
  const [username, setUsername] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [lobbyStatus, setLobbyStatus] = useState('idle') // idle | waiting
  const [fleet, setFleet] = useState(DEFAULT_FLEET)
  const [placementBusy, setPlacementBusy] = useState(false)
  const [game, setGame] = useState(null)
  const [notice, setNotice] = useState(null)
  const tokenRef = useRef(null)
  const usernameRef = useRef('')
  const phaseRef = useRef('login')

  useEffect(() => {
    phaseRef.current = phase
  }, [phase])

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
      case 'GAME_CREATED':
        setLobbyStatus('waiting')
        setError(null)
        break
      case 'PLACEMENT':
        setFleet(msg.fleet || DEFAULT_FLEET)
        setLobbyStatus('idle')
        setPlacementBusy(false)
        setError(null)
        setPhase('placement')
        break
      case 'GAME_START':
        setGame({
          sessionId: msg.session_id,
          players: msg.players || [],
          currentTurn: msg.current_turn,
          own: msg.your_board || emptyBoard(),
          tracking: emptyBoard(),
        })
        setLobbyStatus('idle')
        setPlacementBusy(false)
        setError(null)
        setPhase('game')
        break
      case 'MOVE_RESULT':
        setNotice(null)
        setGame((prev) => {
          if (!prev) return prev
          const mark = HIT_MARKS.has(msg.result) ? 'X' : 'o'
          if (msg.by === usernameRef.current) {
            return { ...prev, tracking: withCell(prev.tracking, msg.x, msg.y, mark), currentTurn: msg.next_turn }
          }
          return { ...prev, own: withCell(prev.own, msg.x, msg.y, mark), currentTurn: msg.next_turn }
        })
        break
      case 'GAME_END':
        setGame((prev) =>
          prev ? { ...prev, over: true, result: { winner: msg.winner, reason: msg.reason } } : prev,
        )
        break
      case 'ERROR':
        if (phaseRef.current === 'game') {
          setNotice(msg.message || msg.code)
        } else if (phaseRef.current === 'placement') {
          setPlacementBusy(false)
          setError(msg.message || msg.code)
        } else {
          setBusy(false)
          setLobbyStatus('idle')
          setError(msg.message || msg.code)
        }
        break
      case '__DISCONNECTED__':
        setError('Utracono połączenie z mostem.')
        setPhase('login')
        setLobbyStatus('idle')
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
      usernameRef.current = user
      const hash = await sha256Hex(password)
      send('AUTH', { username: user, password_hash: hash })
    },
    [send],
  )

  const handleCreate = useCallback(() => {
    setError(null)
    send('CREATE_GAME')
  }, [send])

  const handleJoin = useCallback(() => {
    setError(null)
    send('JOIN_GAME')
  }, [send])

  const handleFire = useCallback(
    (x, y) => {
      send('MOVE', { x, y })
    },
    [send],
  )

  const handlePlacement = useCallback(
    (ships) => {
      setPlacementBusy(true)
      setError(null)
      send('PLACE_SHIPS', { ships })
    },
    [send],
  )

  const backToLobby = useCallback(() => {
    setGame(null)
    setNotice(null)
    setError(null)
    setLobbyStatus('idle')
    setPhase('lobby')
  }, [])

  return (
    <div className="app">
      <h1>STATKI</h1>
      {phase === 'login' && (
        <Login onSubmit={handleLogin} error={error} busy={busy} connected={connected} />
      )}
      {phase === 'lobby' && (
        <Lobby
          username={username}
          status={lobbyStatus}
          onCreate={handleCreate}
          onJoin={handleJoin}
          error={error}
        />
      )}
      {phase === 'placement' && (
        <Placement fleet={fleet} onConfirm={handlePlacement} busy={placementBusy} error={error} />
      )}
      {phase === 'game' && game && (
        <Game
          game={game}
          username={username}
          onFire={handleFire}
          notice={notice}
          onBack={backToLobby}
        />
      )}
    </div>
  )
}
