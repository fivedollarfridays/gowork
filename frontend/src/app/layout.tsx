import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/lib/providers";
import { MotionProvider } from "@/lib/motion";
import { SmoothScroll } from "@/components/SmoothScroll";
import { ScrollProgress } from "@/components/ScrollProgress";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { TranslationProvider } from "@/hooks/useTranslation";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ViewTransitionsProvider } from "@/components/ViewTransitionsProvider";
import { SkipToContent } from "@/components/wall/SkipToContent";
import {
  AriaLiveProvider,
  AriaLiveRegion,
} from "@/components/wall/AriaLiveRegion";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const SITE_NAME = "GoWork";
const SITE_TAGLINE = "Workforce infrastructure for any American city.";
const SITE_DESCRIPTION = SITE_TAGLINE;

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://gowork.example";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_NAME,
    template: `%s | ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/apple-icon.png", sizes: "180x180", type: "image/png" }],
    shortcut: ["/favicon.ico"],
  },
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    title: `${SITE_NAME} — ${SITE_TAGLINE}`,
    description: SITE_DESCRIPTION,
    images: [
      {
        url: "/og-image.svg",
        width: 1200,
        height: 630,
        alt: `${SITE_NAME} — ${SITE_TAGLINE}`,
      },
    ],
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE_NAME} — ${SITE_TAGLINE}`,
    description: SITE_DESCRIPTION,
    images: ["/og-image.svg"],
  },
};

export const viewport: Viewport = {
  themeColor: "#0A0E1A",
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
              <AriaLiveProvider>
                <ScrollProgress />
                <ViewTransitionsProvider>
                  <TranslationProvider>
                    <SkipToContent />
                  </TranslationProvider>
                  <Header />
                  <ErrorBoundary>
                    <main
                      id="main"
                      className="flex min-h-[calc(100vh-3.5rem)] flex-col"
                    >
                      <div className="flex-1">{children}</div>
                      <TranslationProvider>
                        <Footer />
                      </TranslationProvider>
                    </main>
                  </ErrorBoundary>
                  <AriaLiveRegion />
                </ViewTransitionsProvider>
              </AriaLiveProvider>
            </SmoothScroll>
          </MotionProvider>
        </Providers>
      </body>
    </html>
  );
}
