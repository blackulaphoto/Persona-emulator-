/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== 'production'
const devApiBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '')

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (!isDev) return []
    return [
      {
        // Proxy API calls to the local backend during development only.
        source: '/api/:path*',
        destination: `${devApiBase}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
