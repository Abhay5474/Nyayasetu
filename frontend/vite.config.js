import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // same-origin /api in dev and in production (nginx), so no CORS configuration is needed
      // changeOrigin stays false so the Host header still matches the browser's Origin (same-origin for Spring's CORS check)
      '/api': { target: process.env.VITE_API_PROXY || 'http://localhost:8080', changeOrigin: false },
    },
  },
  test: { environment: 'node' },
});
