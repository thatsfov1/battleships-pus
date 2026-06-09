import { BOARD_SIZE, COLS } from './config'

export const emptyBoard = () =>
  Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill(''))

// 'B5' <-> (x, y); kolumna A..J = x, wiersz 1..10 = y+1
export const coordLabel = (x, y) => `${COLS[x]}${y + 1}`

// Ustawia komorke w nowej kopii planszy (immutability dla Reacta).
export function withCell(board, x, y, value) {
  return board.map((row, ry) =>
    ry === y ? row.map((cell, cx) => (cx === x ? value : cell)) : row,
  )
}
