import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api':    { target: 'http://localhost:8000', changeOrigin: false },
      '/auth':   { target: 'http://localhost:8000', changeOrigin: false },
      '/admin':  { target: 'http://localhost:8000', changeOrigin: false },
      '/static': { target: 'http://localhost:8000', changeOrigin: false },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.js'],
    coverage: {
      provider: 'v8',
      thresholds: { lines: 80 },
    },
  },
});
