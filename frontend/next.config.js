/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  basePath: '/app',
  assetPrefix: '/app/',
  images: { unoptimized: true },
  webpack: (config) => {
    // Ensure @/ alias works in webpack
    config.resolve.alias['@'] = path.resolve(__dirname);
    return config;
  },
}

module.exports = nextConfig
