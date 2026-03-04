import withPWA from "next-pwa";

const withPwa = withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development"
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Permitir origens de desenvolvimento
  allowedDevOrigins: ['10.2.0.2'],
  
  // Configuração para produção
  env: {
    // URL público da API (usado pelo cliente/browser)
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    // URL público da Aplicação
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  },
  
  // Otimizações de imagem
  images: {
    domains: ['res.cloudinary.com', 'localhost'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Headers de segurança
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
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          }
        ],
      },
    ];
  },
  
  // Proxy para backend Flask (usado pelo servidor Next.js)
  async rewrites() {
    // URL interno do backend (pode ser diferente do público, ex: http://backend:5000 no Docker)
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      // Proxy para uploads públicos (imagens de safras, perfil)
      {
        source: '/uploads/public/:path*',
        destination: `${backendUrl}/uploads/public/:path*`,
      }
    ];
  },
};

export default withPwa(nextConfig);
