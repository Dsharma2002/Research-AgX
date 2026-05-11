import './globals.css'

export const metadata = {
  title: 'Research AGX',
  description: 'A multi-agent research pipeline',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
