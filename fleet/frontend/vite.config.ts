import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // publicDir defaults to 'public' — prepare_map.py outputs map_config.js and map PNG here
  // build.outDir defaults to 'dist' — FastAPI should serve from fleet/frontend/dist/
})
