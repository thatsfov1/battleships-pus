import Board from './Board'

export default function Game({ game, username, onFire }) {
  const myTurn = game.currentTurn === username && !game.over

  return (
    <div className="game">
      <div className={`turn ${myTurn ? 'mine' : 'theirs'}`}>
        {game.over
          ? 'Gra zakończona'
          : myTurn
            ? 'Twoja tura — kliknij pole na planszy przeciwnika'
            : `Tura przeciwnika (${game.currentTurn || '—'})`}
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
    </div>
  )
}
