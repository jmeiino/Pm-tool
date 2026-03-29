import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "PM-Tool — Persönliches Projektmanagement",
  description: "Dein persönliches Projektmanagement-Dashboard",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="font-sans bg-surface-bg">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
