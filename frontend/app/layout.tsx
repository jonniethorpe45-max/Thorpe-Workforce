import "./globals.css";

import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"),
  title: {
    default: "Thorpe Workforce",
    template: "%s | Thorpe Workforce"
  },
  description: "Deploy AI workers for sales, marketing, research, and operations.",
  openGraph: {
    title: "Thorpe Workforce",
    description: "Deploy AI workers for sales, marketing, research, and operations.",
    type: "website",
    url: "/",
    siteName: "Thorpe Workforce"
  },
  twitter: {
    card: "summary_large_image",
    title: "Thorpe Workforce",
    description: "Deploy AI workers for sales, marketing, research, and operations."
  }
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
