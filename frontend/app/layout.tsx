import './globals.css'
import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { AuthProvider } from '../contexts/AuthContext'

export const metadata: Metadata = {
  title: 'Rubicks | AI Life Simulation',
  description: 'AI-powered psychological development simulations. Explore how life experiences shape personality over time.',

  // Open Graph (Facebook, LinkedIn, etc.)
  openGraph: {
    title: 'Rubicks',
    description: 'AI-powered psychological development simulations. Explore how life experiences shape personality over time.',
    url: 'https://persona-emulator.vercel.app',
    siteName: 'Rubicks',
    images: [
      {
        url: '/landing-hero.png',
        width: 1672,
        height: 941,
        alt: 'Rubicks',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },

  // Twitter Card
  twitter: {
    card: 'summary_large_image',
    title: 'Rubicks',
    description: 'AI-powered psychological development simulations',
    images: ['/landing-hero.png'],
  },

  // Favicon
  icons: {
    icon: '/rubicks-icon.png',
    apple: '/rubicks-icon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
