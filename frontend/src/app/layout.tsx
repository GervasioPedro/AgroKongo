import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AgroKongo - O Mercado Agrícola de Angola",
  description: "Conectando produtores e compradores em Angola.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-AO">
      <body className={inter.className}>
        {/* Aqui podemos adicionar um AuthProvider no futuro */}
        <main>{children}</main>
      </body>
    </html>
  );
}