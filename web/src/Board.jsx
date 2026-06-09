import { Fragment } from 'react'
import { COLS } from './config'

const CELL_CLASS = {
  '': 'empty',
  S: 'ship',
  X: 'hit',
  o: 'miss',
  sunk: 'sunk',
}

export default function Board({ board, title, clickable = false, onCell }) {
  return (
    <div className="board-wrap">
      <h3>{title}</h3>
      <div className="board">
        <div className="cell head" />
        {COLS.split('').map((c) => (
          <div key={`c${c}`} className="cell head">
            {c}
          </div>
        ))}
        {board.map((row, y) => (
          <Fragment key={`r${y}`}>
            <div className="cell head">{y + 1}</div>
            {row.map((value, x) => {
              const firable = clickable && value === ''
              return (
                <button
                  key={`${x}-${y}`}
                  type="button"
                  className={`cell ${CELL_CLASS[value] || 'empty'}${firable ? ' firable' : ''}`}
                  disabled={!firable}
                  onClick={() => firable && onCell(x, y)}
                  aria-label={`${COLS[x]}${y + 1}`}
                >
                  {value === 'sunk' ? '💥' : ''}
                </button>
              )
            })}
          </Fragment>
        ))}
      </div>
    </div>
  )
}
