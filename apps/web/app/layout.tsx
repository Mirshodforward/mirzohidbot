import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Mirzohid — magazin ijarasi boshqaruvi",
    template: "%s · Mirzohid",
  },
  description:
    "Magazin ijarasi, qarz va elektr hisobini bir joyda yuriting. Telegram bot, Mini App va sayt — bitta tizim.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1, // Mini App'da qo'sh-tap zoom noqulaylik tug'diradi
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#17212b" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <head>
        {/*
          Rasmiy Telegram skripti. `beforeInteractive` — React hidratsiyasidan
          oldin yuklanadi, shuning uchun `window.Telegram.WebApp` birinchi
          renderdayoq tayyor bo'ladi.
        */}
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
