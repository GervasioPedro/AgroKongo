import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AgroKongo - Marketplace Agrícola com Escrow",
  description: "Plataforma de intermediação agrícola com sistema de custódia financeira para Angola",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-AO">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
