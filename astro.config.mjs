import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import cloudflare from '@astrojs/cloudflare';

// https://astro.build/config
export default defineConfig({
  output: 'server',
  adapter: cloudflare({
    imageService: 'compile',
  }),

  integrations: [
    react(),
    tailwind({
      applyBaseStyles: false,
    }),
  ],

  vite: {
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    optimizeDeps: {
      exclude: ['@supabase/supabase-js'],
    },
  },

  // Image optimization
  image: {
    domains: ['supabase.co', 'flagcdn.com', 'github.com', 'avatars.githubusercontent.com'],
  },

  // Security headers
  server: {
    headers: {
      'X-Frame-Options': 'SAMEORIGIN',
      'X-Content-Type-Options': 'nosniff',
      'X-XSS-Protection': '1; mode=block',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    },
  },

  // Build optimizations
  build: {
    inlineStylesheets: 'auto',
  },

  // Redirects from Next.js config
  redirects: {
    '/chat': '/',
    '/posts': '/',
    '/community/[...path]': '/communities/[...path]',
  },
});
