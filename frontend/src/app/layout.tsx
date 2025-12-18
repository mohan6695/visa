import './globals.css'

export const metadata = {
  title: 'Visa Platform - Your Gateway to Global Travel',
  description: 'Comprehensive visa information, community discussions, and AI-powered assistance for travelers worldwide.',
  keywords: 'visa, travel, immigration, embassy, passport, country information, visa requirements',
  authors: [{ name: 'Visa Platform Team' }],
  creator: 'Visa Platform',
  publisher: 'Visa Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <main>
          {children}
        </main>
      </body>
    </html>
  )
}