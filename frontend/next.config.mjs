import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== 'production';
const nextConfig = {
  compress: true,
  poweredByHeader: false,
  experimental: {
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  async headers() {
    // connect-src: include localhost only in dev (S-M5).
    // Dev allows any localhost port so test backends on alternate ports
    // (e.g. Playwright using :8888 vs the canonical :8000) aren't blocked.
    const connectSrc = isDev
      ? "connect-src 'self' http://localhost:* http://127.0.0.1:* https://*.railway.app https://*.up.railway.app"
      : "connect-src 'self' https://*.montgowork.com https://*.railway.app https://*.up.railway.app";

    const securityHeaders = [
      { key: 'X-Frame-Options', value: 'DENY' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      {
        key: 'Permissions-Policy',
        value: 'camera=(), microphone=(), geolocation=()',
      },
      {
        key: 'Content-Security-Policy',
        value: [
          "default-src 'self'",
          // unsafe-inline required: Next.js injects inline styles for CSS-in-JS
          // and inline scripts for __NEXT_DATA__. Cannot use nonce without custom server.
          `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''}`,
          "style-src 'self' 'unsafe-inline'",
          "img-src 'self' data: blob:",
          "font-src 'self' data:",
          connectSrc,
        ].join('; '),
      },
    ];

    // HSTS in production only (S-M4)
    if (!isDev) {
      securityHeaders.push({
        key: 'Strict-Transport-Security',
        value: 'max-age=63072000; includeSubDomains',
      });
    }

    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
};

export default withBundleAnalyzer(nextConfig);
