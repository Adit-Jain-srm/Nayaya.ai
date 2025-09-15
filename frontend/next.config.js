/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Nayaya.ai',
    NEXT_PUBLIC_MAX_FILE_SIZE_MB: process.env.NEXT_PUBLIC_MAX_FILE_SIZE_MB || '10',
  },
  webpack: (config) => {
    config.resolve.alias.canvas = false;
    return config;
  },
  // Enable standalone output for Docker deployment
  output: 'standalone',
  // Optimize images
  images: {
    domains: ['storage.googleapis.com'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
}

module.exports = nextConfig
