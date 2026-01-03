/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export', // Static export for Nginx serving
  trailingSlash: true, // Required for static export routing
  images: {
    unoptimized: true, // Required for static export
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig

