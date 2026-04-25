import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from '@/lib/providers';
import { MotionProvider } from '@/lib/motion';
import { SmoothScroll } from '@/components/SmoothScroll';
import { ScrollProgress } from '@/components/ScrollProgress';
import { Header } from '@/components/layout/Header';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ViewTransitionsProvider } from '@/components/ViewTransitionsProvider';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

const SITE_DESCRIPTION =
  'Workforce Navigator — overcome barriers and find your path to employment';

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? 'https://montgowork.com';

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'MontGoWork',
    template: '%s | MontGoWork',
  },
  description: SITE_DESCRIPTION,
  applicationName: 'MontGoWork',
  manifest: '/manifest.json',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    shortcut: ['/favicon.ico'],
  },
  openGraph: {
    type: 'website',
    siteName: 'MontGoWork',
    title: 'MontGoWork — Workforce Navigator',
    description: SITE_DESCRIPTION,
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'MontGoWork — Workforce Navigator',
      },
    ],
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MontGoWork — Workforce Navigator',
    description: SITE_DESCRIPTION,
    images: ['/og-image.png'],
  },
};

export const viewport: Viewport = {
  themeColor: '#1c3461',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <MotionProvider>
            <SmoothScroll>
              <ScrollProgress />
              <ViewTransitionsProvider>
                <Header />
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
              </ViewTransitionsProvider>
            </SmoothScroll>
          </MotionProvider>
        </Providers>
      </body>
    </html>
  );
}
