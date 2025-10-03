import type React from "react";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { AuthProvider } from "@/lib/AuthContext";
import { Toaster } from "@/components/ui/sonner";
import { Analytics } from "@vercel/analytics/next"
import "./globals.css";

const inter = Inter({ subsets: ["latin"], display: "swap", preload: false });

export const metadata: Metadata = {
  title: "PianoFi - Turn Any Song Into Piano Sheet Music",
  description:
    "Upload any audio file and get professional piano sheet music in minutes. Powered by advanced AI models.",
  metadataBase: new URL("https://www.pianofi.ca"),
  alternates: {
    canonical: "./",
  },
  icons: {
    icon: [
      { url: "/favicon.ico" },
    ],
    apple: [
      { url: "/favicon.ico" },
    ],
  },

  other: {
    'apple-mobile-web-app-title': 'Pianofi',
    'mobile-web-app-capable': 'yes',
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="apple-touch-icon" sizes="180x180" href="/icon_logo.png" />
        <link rel="apple-touch-icon" sizes="152x152" href="/icon_logo.png" />
        <link rel="apple-touch-icon" sizes="167x167" href="/icon_logo.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/icon_logo.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/icon_logo.png" />
        <link rel="shortcut icon" href="/favicon.ico" />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            {children}
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  );
}
