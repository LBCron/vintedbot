import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/bulk': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/analytics': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/automation': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/accounts': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/billing': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/temp_photos': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
