// webui/vite.config.js
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load environment variables from system process.env and .env files
  const env = loadEnv(mode, process.cwd(), '');
  const apiPort = env.API_PORT || '8000'; // Default fallback to 8000

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: `http://localhost:${apiPort}`,
          changeOrigin: true,
          ws: true
        }
      }
    }
  }
})