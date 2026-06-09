import Board from './Board'

function ScoreCounter({ label, value, total, danger }) {
  return (
    <div className={`score ${danger ? 'danger' : ''}`}>
      <span className="score-label">{label}</span>
      <span className="score-value" key={value}>
        {value}/{total}
      </span>
      <span className="pips">
        {Array.from({ length: total }, (_, i) => (
          <i key={i} className={`pip ${i < value ? 'on' : ''}`} />
        ))}
      </span>
    </div>
  )
}

function resultText(result, username) {
  if (!result) return ''
  const reason = result.reason === 'DISCONNECT' ? ' (przeciwnik się rozłączył)' : ''
  if (result.winner === username) return `Zatopiłeś całą flotę przeciwnika!${reason}`
  if (result.winner) return `Wygrywa ${result.winner}.${reason}`
  return 'Gra zakończona bez rozstrzygnięcia.'
}

export default function Game({ game, username, onFire, notice, onBack }) {
  const myTurn = game.currentTurn === username && !game.over
  const won = game.result?.winner === username

  return (
    <div className="game">
      <div className={`turn ${myTurn ? 'mine' : 'theirs'}`}>
        {game.over
          ? 'Gra zakończona'
          : myTurn
            ? 'Twoja tura — kliknij pole na planszy przeciwnika'
            : `Tura przeciwnika (${game.currentTurn || '—'})`}
      </div>

      {notice && <div className="notice">{notice}</div>}

      <div className="counters">
        <ScoreCounter label="Zatopione przeciwnika" value={game.enemySunk} total={game.fleetCount} />
        <ScoreCounter label="Twoje straty" value={game.mySunk} total={game.fleetCount} danger />
      </div>

      <div className="boards">
        <Board board={game.own} title="Twoja plansza" />
        <Board
          board={game.tracking}
          title="Plansza przeciwnika"
          clickable={myTurn}
          onCell={onFire}
        />
      </div>

      <div className="legend">
        <span><i className="swatch ship" /> statek</span>
        <span><i className="swatch hit" /> trafienie</span>
        <span><i className="swatch miss" /> pudło</span>
      </div>

      {game.over && (
        <div className="overlay">
          <div className="modal">
            <h2 className={won ? 'ok' : 'bad'}>{won ? 'ZWYCIĘSTWO 🎉' : 'PORAŻKA'}</h2>
            <p className="muted">{resultText(game.result, username)}</p>
            <button type="button" onClick={onBack}>
              Powrót do lobby
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
