/** @type {import('next').NextConfig} */
const nextConfig = {
  // Activer le mode strict de React
  reactStrictMode: true,

  // Configuration des images (si besoin)
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Variables d'environnement publiques
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Headers de sécurité
  async headers() {
    return [
      {
        source: '/:path*',
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
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Redirections (si besoin)
  async redirects() {
    return [];
  },

  // Rewrites pour proxy API (optionnel, utile en développement)
  async rewrites() {
    return [
      // Décommentez pour proxifier les appels API en dev
      // {
      //   source: '/api/:path*',
      //   destination: 'http://localhost:8000/:path*',
      // },
    ];
  },
};

module.exports = nextConfig;