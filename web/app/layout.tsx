import type { Metadata } from 'next'
import './globals.css'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'FinanceAI - AI-Powered Stock Analysis',
  description: 'AI-powered stock analysis platform for Korean and US markets',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 lg:ml-0 overflow-x-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
