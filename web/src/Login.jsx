import { useState } from 'react'

export default function Login({ onSubmit, error, busy, connected }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const submit = (e) => {
    e.preventDefault()
    if (username && password) onSubmit(username, password)
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Logowanie</h2>
      <label>
        Login
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
      </label>
      <label>
        Hasło
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>
      <button type="submit" disabled={!connected || busy}>
        {busy ? 'Logowanie…' : 'Zaloguj'}
      </button>
      {!connected && <p className="muted">Łączenie z mostem…</p>}
      {error && <p className="bad">{error}</p>}
      <p className="muted small">Konta testowe: user1/pass1, user2/pass2</p>
    </form>
  )
}
