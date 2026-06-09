import { BOARD_SIZE } from './config'

const randInt = (n) => Math.floor(Math.random() * n)

export function cellsFor(x, y, len, horizontal) {
  const cells = []
  for (let i = 0; i < len; i++) cells.push(horizontal ? [x + i, y] : [x, y + i])
  return cells
}

export function inBounds(cells) {
  return cells.every(([x, y]) => x >= 0 && x < BOARD_SIZE && y >= 0 && y < BOARD_SIZE)
}

// Czy pola nakladaja sie lub stykaja (krawedzia/rogiem) z juz zajetymi.
export function touchesOrOverlaps(cells, occupied) {
  for (const [x, y] of cells) {
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        if (occupied.has(`${x + dx},${y + dy}`)) return true
      }
    }
  }
  return false
}

export function occupiedSet(ships) {
  const s = new Set()
  for (const ship of ships) for (const [x, y] of ship.cells) s.add(`${x},${y}`)
  return s
}

// Losowe, poprawne rozmieszczenie floty (statki nie stykaja sie).
export function randomFleet(sizes) {
  const ships = []
  const occ = new Set()
  for (const len of sizes) {
    for (let tries = 0; tries < 1000; tries++) {
      const horizontal = Math.random() < 0.5
      const x = horizontal ? randInt(BOARD_SIZE - len + 1) : randInt(BOARD_SIZE)
      const y = horizontal ? randInt(BOARD_SIZE) : randInt(BOARD_SIZE - len + 1)
      const cells = cellsFor(x, y, len, horizontal)
      if (!touchesOrOverlaps(cells, occ)) {
        ships.push({ len, cells })
        for (const [cx, cy] of cells) occ.add(`${cx},${cy}`)
        break
      }
    }
  }
  return ships
}
