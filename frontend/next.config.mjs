const backend = process.env.BACKEND_URL || 'http://backend:8000';

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${backend}/api/:path*` },
      { source: '/uploads/:path*', destination: `${backend}/uploads/:path*` },
      { source: '/health', destination: `${backend}/health` }
    ];
  }
};

export default nextConfig;
