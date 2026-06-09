import { Fragment, useEffect, useMemo, useState } from 'react'
import { BOARD_SIZE, COLS } from './config'
import { cellsFor, inBounds, touchesOrOverlaps, occupiedSet, randomFleet } from './placementUtils'

export default function Placement({ fleet, onConfirm, busy, error }) {
  const buildToPlace = () => fleet.map((len, id) => ({ id, len }))
  const [placed, setPlaced] = useState([])
  const [toPlace, setToPlace] = useState(buildToPlace)
  const [horizontal, setHorizontal] = useState(true)
  const [hover, setHover] = useState(null)

  const selected = toPlace[0] || null
  const occupied = useMemo(() => occupiedSet(placed), [placed])
  const allPlaced = placed.length === fleet.length

  const preview = useMemo(() => {
    if (!selected || !hover) return null
    const cells = cellsFor(hover.x, hover.y, selected.len, horizontal)
    return { cells, ok: inBounds(cells) && !touchesOrOverlaps(cells, occupied) }
  }, [selected, hover, horizontal, occupied])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'r' || e.key === 'R') setHorizontal((h) => !h)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const handleCell = (x, y) => {
    if (busy) return
    const key = `${x},${y}`
    const existing = placed.find((s) => s.cells.some(([cx, cy]) => `${cx},${cy}` === key))
    if (existing) {
      setPlaced((p) => p.filter((s) => s !== existing))
      setToPlace((t) => [{ id: existing.id, len: existing.len }, ...t])
      return
    }
    if (!selected) return
    const cells = cellsFor(x, y, selected.len, horizontal)
    if (!inBounds(cells) || touchesOrOverlaps(cells, occupied)) return
    setPlaced((p) => [...p, { id: selected.id, len: selected.len, cells }])
    setToPlace((t) => t.slice(1))
  }

  const doRandom = () => {
    setPlaced(randomFleet(fleet).map((s, id) => ({ id, len: s.len, cells: s.cells })))
    setToPlace([])
  }
  const reset = () => {
    setPlaced([])
    setToPlace(buildToPlace())
  }

  const previewSet = preview ? new Set(preview.cells.map(([x, y]) => `${x},${y}`)) : null

  return (
    <div className="card placement">
      <h2>Rozmieść statki</h2>
      <p className="muted small">
        Klik = postaw · klik na statek = usuń · „R" lub „Obróć" = orientacja. Statki nie mogą się
        stykać krawędzią ani rogiem.
      </p>
      <div className="board">
        <div className="cell head" />
        {COLS.split('').map((c) => (
          <div key={`c${c}`} className="cell head">
            {c}
          </div>
        ))}
        {Array.from({ length: BOARD_SIZE }, (_, y) => (
          <Fragment key={`r${y}`}>
            <div className="cell head">{y + 1}</div>
            {Array.from({ length: BOARD_SIZE }, (_, x) => {
              const key = `${x},${y}`
              let cls = 'empty'
              if (occupied.has(key)) cls = 'ship'
              else if (previewSet?.has(key)) cls = preview.ok ? 'preview-ok' : 'preview-bad'
              return (
                <button
                  key={`${x}-${y}`}
                  type="button"
                  className={`cell ${cls}`}
                  onMouseEnter={() => setHover({ x, y })}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => handleCell(x, y)}
                />
              )
            })}
          </Fragment>
        ))}
      </div>

      <div className="fleet-list">
        Do rozmieszczenia:{' '}
        {toPlace.length ? toPlace.map((s) => `${s.len}-masztowy`).join(', ') : 'wszystko ustawione ✓'}
      </div>

      <div className="placement-actions">
        <button type="button" className="secondary" onClick={() => setHorizontal((h) => !h)}>
          Obróć ({horizontal ? 'poziomo' : 'pionowo'})
        </button>
        <button type="button" className="secondary" onClick={doRandom}>
          Losuj
        </button>
        <button type="button" className="secondary" onClick={reset}>
          Wyczyść
        </button>
        <button type="button" onClick={() => onConfirm(placed.map((s) => s.cells))} disabled={!allPlaced || busy}>
          Gotowe
        </button>
      </div>

      {error && <p className="bad">{error}</p>}
      {busy && <p className="muted">Czekam na przeciwnika…</p>}
    </div>
  )
}
