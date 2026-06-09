// Adres mostu WebSocket (most przekazuje protokol do serwera gry TLS).
// Domyslnie laczymy sie po tym samym origin pod sciezka /ws — dev server Vite
// proxiuje ten ruch do mostu na localhost:8765 (patrz vite.config.js). Dzieki
// temu przez tunel (np. ngrok) wystarczy wystawic JEDEN port (5173): zarowno
// strona, jak i WebSocket ida przez ten sam publiczny adres.
// Pelny adres mostu mozna nadal wymusic zmienna VITE_GATEWAY_URL.
function defaultGateway() {
  if (typeof window === 'undefined') return 'ws://localhost:8765'
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws`
}

export const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || defaultGateway()

export const BOARD_SIZE = 10
export const COLS = 'ABCDEFGHIJ'
