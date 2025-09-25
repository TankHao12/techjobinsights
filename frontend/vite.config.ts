import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core libraries
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          
          // Data visualization libraries
          'charts': ['recharts', '@react-three/fiber', '@react-three/drei'],
          
          // UI libraries
          'ui-vendor': ['@headlessui/react', '@heroicons/react', 'framer-motion', 'lucide-react'],
          
          // State management and data fetching
          'state-vendor': ['zustand', '@tanstack/react-query', 'axios'],
        },
      },
    },
    // Increase chunk size warning limit if needed (default is 500 kB)
    chunkSizeWarningLimit: 600,
  },
})
