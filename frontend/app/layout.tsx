import "./globals.css";

import type { Metadata } from "next";
import type { ReactNode } from "react";
import { getPublicAppUrl } from "@/lib/runtimeConfig";

const appUrl = getPublicAppUrl();

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
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
