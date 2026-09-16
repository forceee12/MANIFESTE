import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// En développement, /api est relayé vers FastAPI : le navigateur ne voit qu'une
// seule origine, ce qui évite toute question de CORS côté front.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
