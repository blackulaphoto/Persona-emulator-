/**
 * Root Layout with Metadata and Header
 * 
 * Replace: frontend/app/layout.tsx
 */
import type { Metadata } from 'next';
import { AuthProvider } from '@/contexts/AuthContext';
import { Header } from '@/components/Header';
import './globals.css';

export const metadata: Metadata = {
  title: 'Persona Evolution Simulator | LifeStream Labs',
  description: 'AI-powered psychological development simulations. Explore how life experiences shape personality over time using evidence-based psychology.',
  
  // Open Graph (Facebook, LinkedIn, Discord)
  openGraph: {
    title: 'Persona Evolution Simulator',
    description: 'AI-powered psychological development simulations for education and research',
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
  
  // Favicon and App Icons
  icons: {
    icon: '/logo.png',
    apple: '/logo.png',
    shortcut: '/logo.png',
  },
  
  // Additional metadata
  keywords: [
    'psychology',
    'simulation',
    'personality development',
    'AI',
    'education',
    'research',
    'developmental psychology',
    'therapy',
  ],
  authors: [{ name: 'LifeStream Labs' }],
  creator: 'LifeStream Labs',
  publisher: 'LifeStream Labs',
  
  // Viewport
  viewport: {
    width: 'device-width',
    initialScale: 1,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#1a1d20] text-[#F8F6F1]">
        <AuthProvider>
          <Header />
          <main>
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
