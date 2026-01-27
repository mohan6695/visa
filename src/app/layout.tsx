import type { Metadata } from 'next';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'Visa Platform - Your Gateway to Global Travel',
  description: 'Comprehensive visa information, community discussions, and AI-powered assistance for travelers worldwide.',
  keywords: 'visa, travel, immigration, embassy, passport, country information, visa requirements',
  authors: [{ name: 'Visa Platform Team' }],
  openGraph: {
    type: 'website',
    title: 'Visa Platform - Your Gateway to Global Travel',
    description: 'Comprehensive visa information, community discussions, and AI-powered assistance for travelers worldwide.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Visa Platform - Your Gateway to Global Travel',
    description: 'Comprehensive visa information, community discussions, and AI-powered assistance for travelers worldwide.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="SAMEORIGIN" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_PUBLISHER_ID" crossOrigin="anonymous"></script>
      </head>
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  );
}
