import "bootstrap/dist/css/bootstrap.min.css";
import '../styles/globals.css'
import type { Metadata } from 'next'
import { Aboreto, Abril_Fatface, Bellota, Bellota_Text, Big_Shoulders_Display, Comfortaa, Contrail_One, Expletus_Sans, Faster_One, Inter, Jura, Lato, Megrim, Montserrat, Nixie_One, Open_Sans, Patua_One, Pompiere, Poppins, REM, Raleway, Roboto, Share_Tech } from 'next/font/google'
import styles from '../styles/layout.module.css'
import Sidebar from "@/components/Sidebar.server";
const poppins = Poppins({ subsets: ['latin'], weight: "300"})

export const metadata: Metadata = {
  title: 'Item Warehouse',
  description: 'A database with an API in front of it.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={poppins.className}>
        <div className={styles.container}>
            <Sidebar />
            <div className={styles.content}>
                {children}
            </div>
        </div>
      </body>
    </html>
  )
}
