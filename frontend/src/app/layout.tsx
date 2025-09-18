import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers/Providers';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Prompt Lab - Chatbot Laboratory',
  description: 'Un mini-laboratorio de prompts para experimentar con múltiples LLM providers y analizar respuestas automáticamente.',
  keywords: ['AI', 'LLM', 'Chatbot', 'Prompt Engineering', 'Analytics'],
  authors: [{ name: 'Prompt Lab Team' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={inter.variable}>
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
