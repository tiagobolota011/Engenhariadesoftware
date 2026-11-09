/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// O frontend usa a API pela mesma origem: em desenvolvimento, /api é encaminhado para o Django.
const apiTarget = process.env.VITE_API_PROXY ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Sem changeOrigin: o Host mantém-se igual ao Origin do navegador, como exige o CSRF do Django.
      '/api': { target: apiTarget },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
