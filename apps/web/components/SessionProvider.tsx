"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useState } from "react";

import { ApiError, api, type Me } from "@/lib/api";
import { getWebApp, waitForWebApp } from "@/lib/telegram";

interface SessionValue {
  me: Me | null;
  loading: boolean;
  /** Telegram ichidamiz — sarlavha, orqaga tugma va h.k. Telegram beradi. */
  inTelegram: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const SessionContext = createContext<SessionValue>({
  me: null,
  loading: true,
  inTelegram: false,
  error: null,
  refresh: async () => {},
});

export const useSession = () => useContext(SessionContext);

/** Telegram mavzusini CSS o'zgaruvchilarga ko'chiradi. */
function applyTelegramTheme(): void {
  const wa = getWebApp();
  if (!wa) return;
  const root = document.documentElement;
  root.dataset.tgTheme = wa.colorScheme;

  const map: Record<string, string> = {
    bg_color: "--tg-bg",
    text_color: "--tg-text",
    hint_color: "--tg-hint",
    secondary_bg_color: "--tg-card",
    section_separator_color: "--tg-border",
    button_color: "--tg-accent",
  };
  for (const [tgKey, cssVar] of Object.entries(map)) {
    const value = wa.themeParams?.[tgKey];
    if (value) root.style.setProperty(cssVar, value);
  }
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [inTelegram, setInTelegram] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setMe(await api.me());
  }

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const wa = await waitForWebApp();
      const initData = wa?.initData ?? "";

      if (wa && initData) {
        // --- Mini App yo'li ---
        wa.ready();
        wa.expand();
        applyTelegramTheme();
        if (!cancelled) setInTelegram(true);

        try {
          // initData imzosi serverda tekshiriladi — bu yerda ishonch yo'q.
          await api.loginTelegram(initData);
          const profile = await api.me();
          if (!cancelled) setMe(profile);
        } catch (err) {
          if (!cancelled) {
            setError(
              err instanceof ApiError ? err.message : "Telegram orqali kirib bo'lmadi.",
            );
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
        return;
      }

      // --- Oddiy brauzer yo'li: cookie sessiyasi bormi? ---
      try {
        const profile = await api.me();
        if (!cancelled) setMe(profile);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/kirish");
          return;
        }
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Server bilan aloqa yo'q.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <SessionContext.Provider value={{ me, loading, inTelegram, error, refresh }}>
      {children}
    </SessionContext.Provider>
  );
}
