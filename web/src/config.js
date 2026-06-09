// Adres mostu WebSocket (most przekazuje protokol do serwera gry TLS).
export const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'ws://localhost:8765'

export const BOARD_SIZE = 10
export const COLS = 'ABCDEFGHIJ'
