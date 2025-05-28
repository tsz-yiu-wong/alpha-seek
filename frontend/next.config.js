/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 's2.coinmarketcap.com',
        pathname: '/static/img/coins/**',
      },
      {
        protocol: 'https',
        hostname: 'dd.dexscreener.com',
        pathname: '/**', // 允许dd.dexscreener.com下的所有路径
      },
    ],
  },
}

module.exports = nextConfig 