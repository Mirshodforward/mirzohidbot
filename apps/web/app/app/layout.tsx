import type { Metadata } from "next";

import { SessionProvider } from "@/components/SessionProvider";

export const metadata: Metadata = {
  title: "Kabinet",
  // Mini App va kabinet sahifalari qidiruvga tushmasin.
  robots: { index: false, follow: false },
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <div className="tg-safe mx-auto min-h-dvh w-full max-w-2xl px-4 py-5">{children}</div>
    </SessionProvider>
  );
}
