import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'homewrecker.ai',
  description: 'Settle your domestic disputes with AI-powered text analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 text-white`}>
        {children}
      </body>
    </html>

)
}