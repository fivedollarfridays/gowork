import type { Metadata } from 'next';

/**
 * Metadata for the token-gated `/shared/[token]` route.
 *
 * Privacy contract:
 * - We MUST NOT include the raw share token, the share-target session id, or
 *   any worker-controlled content (name, plan body, outcomes) in the meta tags.
 *   Embedding tokens in OG/Twitter cards leaks them to link-preview crawlers
 *   (Slack, iMessage, Twitter), which would defeat the purpose of an
 *   unguessable share URL.
 * - We tag the page `noindex, nofollow` so search engines never crawl shared
 *   plan URLs even if a token leaks into a public link.
 * - All copy is generic ("A shared plan") so a Slack preview shows the brand
 *   without revealing the recipient or contents.
 */

const SHARED_DESCRIPTION =
  'A shared plan from MontGoWork — view the action plan without creating an account.';

const SHARED_OG_IMAGE = {
  url: '/og-image.png',
  width: 1200,
  height: 630,
  alt: 'MontGoWork — Shared Plan',
} as const;

interface SharedLayoutMetadataArgs {
  // Next.js 15 makes route params async — params is always a Promise.
  params: Promise<{ token: string }>;
}

export async function generateMetadata(
  _args: SharedLayoutMetadataArgs,
): Promise<Metadata> {
  // Intentionally do NOT resolve the token to share data here. The share
  // payload is intentionally redacted: see SharedPlanView for the reasoning.
  // We only need a generic, brand-safe preview card.
  return {
    title: 'Shared Plan',
    description: SHARED_DESCRIPTION,
    robots: {
      index: false,
      follow: false,
      nocache: true,
      googleBot: { index: false, follow: false },
    },
    openGraph: {
      type: 'website',
      siteName: 'MontGoWork',
      title: 'Shared Plan | MontGoWork',
      description: SHARED_DESCRIPTION,
      images: [SHARED_OG_IMAGE],
      locale: 'en_US',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Shared Plan | MontGoWork',
      description: SHARED_DESCRIPTION,
      images: [SHARED_OG_IMAGE.url],
    },
  };
}

export default function SharedLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <>{children}</>;
}
