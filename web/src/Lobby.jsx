export default function Lobby({ username, status, onCreate, onJoin, error }) {
  return (
    <div className="card">
      <h2>Witaj, {username}!</h2>
      {status === 'waiting' ? (
        <>
          <p className="muted">Gra utworzona. Oczekiwanie na przeciwnika…</p>
          <div className="spinner" aria-hidden="true" />
        </>
      ) : (
        <div className="lobby-actions">
          <button type="button" onClick={onCreate}>
            Utwórz grę
          </button>
          <button type="button" className="secondary" onClick={onJoin}>
            Dołącz do gry
          </button>
        </div>
      )}
      {error && <p className="bad">{error}</p>}
    </div>
  )
}
