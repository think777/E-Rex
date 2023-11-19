import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Head from 'next/head'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'E-Rex',
  description: 'An Event Recommender',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <Head>
        {/* Add this to include your logo as the favicon */}
        <link rel="icon" type="image/png" sizes="16x16" href="/E-Rex-circular.png" />
        {/* Add other meta tags or head elements as needed */}
      </Head>
      <body className={inter.className}>
        <header className="flex items-center p-4">
          {/* Your logo component goes here */}
          <img className="w-32 h-32" src="/E-Rex-circular.png" alt="Logo" />

          {/* Your heading goes here */}
          <h1 className="text-4xl font-bold ml-4">E-Rex.</h1>
          <h2 className="text-4xl italic ml-4">Event Recommender</h2>
        </header>
        {children}
      </body>
    </html>
  )
}
