/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [
      // Apex → www (canonical)
      {
        source: '/:path*',
        has: [{ type: 'host', value: 'pianofi.ca' }],
        destination: 'https://www.pianofi.ca/:path*',
        permanent: true, // 308
      },
    ];
  },
}

export default nextConfig
