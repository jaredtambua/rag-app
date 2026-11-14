import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // The API only allows this origin, so the dev server must not drift to another port.
  server: { port: 5173, strictPort: true },
})
