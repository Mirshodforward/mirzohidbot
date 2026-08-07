import type { Metadata } from "next";

import { AppShell } from "@/components/AppShell";
import { SessionProvider } from "@/components/SessionProvider";

export const metadata: Metadata = {
  title: "Kabinet",
  // Mini App va kabinet sahifalari qidiruvga tushmasin.
  robots: { index: false, follow: false },
};

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <AppShell>{children}</AppShell>
    </SessionProvider>
  );
}
