import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Zezwol na dostep przez dowolny host (np. losowa domena ngrok/cloudflare).
    allowedHosts: true,
    // Proxy WebSocket: przegladarka laczy sie z /ws na tym samym origin,
    // a Vite przekazuje ruch do mostu WebSocket dzialajacego na :8765.
    // Dzieki temu przez tunel wystarczy wystawic tylko port 5173.
    proxy: {
      '/ws': { target: 'ws://localhost:8765', ws: true, changeOrigin: true },
    },
  },
})
