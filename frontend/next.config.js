/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  basePath: '/app',
  assetPrefix: '/app/',
  images: { unoptimized: true },
}

module.exports = nextConfig
