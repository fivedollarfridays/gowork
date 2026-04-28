import type { Metadata } from 'next';

const DAILY_DESCRIPTION =
  'Your daily plan — what to work on today, what to follow up on, and what is next on your path to a job.';

export const metadata: Metadata = {
  title: 'Daily Plan',
  description: DAILY_DESCRIPTION,
  openGraph: {
    type: 'website',
    siteName: 'GoWork',
    title: 'Daily Plan | GoWork',
    description: DAILY_DESCRIPTION,
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'GoWork Daily Plan',
      },
    ],
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Daily Plan | GoWork',
    description: DAILY_DESCRIPTION,
    images: ['/og-image.png'],
  },
};

export default function DailyLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <>{children}</>;
}
