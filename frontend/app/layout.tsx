import type { Metadata } from 'next'
import './globals.css'
import Navigation from '@/components/Navigation'

export const metadata: Metadata = {
  title: 'TikTok Keyword Momentum Tracker',
  description: 'Discover trending TikTok keywords before they peak',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <Navigation />
        {children}
      </body>
    </html>
  )
}

