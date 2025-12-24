import './globals.css'
import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata: Metadata = {
  title: 'Persona Evolution Simulator | LifeStream Labs',
  description: 'AI-powered psychological development simulations. Explore how life experiences shape personality over time.',

  // Open Graph (Facebook, LinkedIn, etc.)
  openGraph: {
    title: 'Persona Evolution Simulator',
    description: 'AI-powered psychological development simulations. Explore how life experiences shape personality over time.',
    url: 'https://persona-emulator.vercel.app',
    siteName: 'Persona Evolution Simulator',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Persona Evolution Simulator - LifeStream Labs',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },

  // Twitter Card
  twitter: {
    card: 'summary_large_image',
    title: 'Persona Evolution Simulator',
    description: 'AI-powered psychological development simulations',
    images: ['/og-image.png'],
  },

  // Favicon
  icons: {
    icon: '/logo.png',
    apple: '/logo.png',
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
