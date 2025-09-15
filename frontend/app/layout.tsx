import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Nayaya.ai - Legal Document Simplification',
  description: 'AI-powered tool to demystify complex legal documents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-primary-600">Nayaya.ai</h1>
                <span className="ml-2 text-sm text-gray-500">Legal Document AI</span>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">⚠️ Educational tool - Not legal advice</span>
              </div>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}
