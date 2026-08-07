"use client";

import { AdminNav } from "@/components/AdminNav";
import { useSession } from "@/components/SessionProvider";

/**
 * Kabinet qobig'i.
 *
 * Pastdagi navigatsiya faqat adminga ko'rsatiladi — oddiy magazin egasining
 * bor-yo'g'i bitta ekrani bor, unga tab kerak emas.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { me } = useSession();
  const isAdmin = Boolean(me?.is_admin);

  return (
    <div
      className={`mx-auto flex min-h-dvh w-full max-w-2xl flex-col px-4 pt-5 ${
        isAdmin ? "" : "tg-safe pb-5"
      }`}
    >
      <div className="flex-1">{children}</div>
      {isAdmin && <AdminNav />}
    </div>
  );
}
