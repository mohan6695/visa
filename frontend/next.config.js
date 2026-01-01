/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  // Performance target: Bundle size <60KB, CSS <12KB
  experimental: {
    // Enable React Server Components
    serverComponentsExternalPackages: ['pg', 'bcrypt', 'redis', '@supabase/supabase-js'],
    
    // Enable Turbopack for faster builds
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
    
    // Edge runtime optimizations
    ppr: true, // Partial Pre-rendering for better TTFB
    optimizeCss: true, // CSS optimization
    optimizeServerReact: true, // React server optimization
    scrollRestoration: true,
    
    // Bundle size optimizations
    bundlePagesExternals: true, // External packages for pages
    optimizeCssForAmp: true, // AMP CSS optimization
  },
  
  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
    // Enable aggressive tree shaking
    reactRemoveProperties: process.env.NODE_ENV === 'production',
    styledComponents: true,
  },
  
  // Enable experimental features for performance
  experimentalOptimizePackageImports: [
    '@supabase/supabase-js',
    'lucide-react',
    'react-hook-form',
    'date-fns',
  ],
  
  // Image optimization with aggressive settings
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    domains: [
      'localhost',
      'supabase.co',
      'github.com',
      'avatars.githubusercontent.com',
      'flagcdn.com',
    ],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.supabase.co',
      },
      {
        protocol: 'https',
        hostname: '*.groq.com',
      },
      {
        protocol: 'https',
        hostname: 'upstash.com',
      },
    ],
  },
  
  // Webpack optimizations for bundle size
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Bundle analyzer for production
    if (!dev && !isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        '@': path.resolve(__dirname, 'src'),
      };
    }
    
    // Optimize for bundle size
    config.optimization = {
      ...config.optimization,
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          default: {
            minChunks: 2,
            priority: -20,
            reuseExistingChunk: true,
          },
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: -10,
            chunks: 'all',
          },
          supabase: {
            test: /[\\/]node_modules[\\/](@supabase|supabase-js)[\\/]/,
            name: 'supabase',
            priority: 10,
            chunks: 'all',
          },
        },
      },
    };
    
    // Remove unused dependencies from bundle
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };
    
    // Bundle analyzer (development only)
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
        })
      );
    }
    
    return config;
  },
  
  // Headers for security and performance
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          },
        ],
      },
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          },
        ],
      },
      {
        source: '/images/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          },
        ],
      },
      {
        source: '/api/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.NODE_ENV === 'production' 
              ? 'https://yourdomain.com' 
              : 'http://localhost:3000',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ];
  },
  
  // Redirects for better SEO and performance
  async redirects() {
    return [
      {
        source: '/chat',
        destination: '/',
        permanent: true,
      },
      {
        source: '/posts',
        destination: '/',
        permanent: true,
      },
      {
        source: '/community/:path*',
        destination: '/communities/:path*',
        permanent: true,
      },
    ];
  },
  
  // Rewrites for PWA
  async rewrites() {
    return [
      {
        source: '/sw.js',
        destination: '/_next/static/sw.js',
      },
    ];
  },
  
  // Environment variables validation
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  
  // Output configuration for edge deployment
  output: 'standalone',
  
  // Build optimizations
  swcMinify: true,
  
  // Enable compression
  compress: true,
  
  // Powered by header
  poweredByHeader: false,
  
  // Trailing slash configuration
  trailingSlash: false,
  
  // Base path configuration
  basePath: '',
  
  // Asset prefix for CDN
  assetPrefix: process.env.NODE_ENV === 'production' ? process.env.CDN_URL : '',
};

module.exports = nextConfig;