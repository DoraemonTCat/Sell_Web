// ===========================================
// Vite Configuration — React SPA
// Configured for Docker development with HMR
// ===========================================
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Accessible from Docker network
    port: 5173,
    watch: {
      usePolling: true, // Required for Docker volume file watching
    },
  },
});
