/**
 * Telegram Mini App bilan ishlash — rasmiy `telegram-web-app.js` ustidan yupqa qatlam.
 *
 * NEGA SDK PAKETI EMAS: `@telegram-apps/*` paketlari deprecated bo'lib
 * `@tma.js/*` ga ko'chdi, va bu ekotizim tez-tez nom almashtirmoqda. Rasmiy
 * skript esa yillar davomida o'zgarmagan va bizga kerak bo'lgan hamma narsani
 * beradi (initData, mavzu, viewport, haptics). Bog'liqlik nolga teng.
 */

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: Record<string, unknown>;
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
  viewportStableHeight?: number;
  ready: () => void;
  expand: () => void;
  close: () => void;
  openTelegramLink: (url: string) => void;
  HapticFeedback?: {
    impactOccurred: (style: "light" | "medium" | "heavy") => void;
    notificationOccurred: (type: "error" | "success" | "warning") => void;
  };
  MainButton?: {
    setText: (t: string) => void;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export function getWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") return null;
  return window.Telegram?.WebApp ?? null;
}

/** Sahifa Telegram ichida ochilganmi? `initData` bo'sh bo'lsa — oddiy brauzer. */
export function isInsideTelegram(): boolean {
  const wa = getWebApp();
  return Boolean(wa && wa.initData && wa.initData.length > 0);
}

/** Skript yuklanishini kutadi (`beforeInteractive` bo'lsa ham poyga bo'lishi mumkin). */
export function waitForWebApp(timeoutMs = 3000): Promise<TelegramWebApp | null> {
  return new Promise((resolve) => {
    const existing = getWebApp();
    if (existing) return resolve(existing);

    const startedAt = Date.now();
    const timer = setInterval(() => {
      const wa = getWebApp();
      if (wa) {
        clearInterval(timer);
        resolve(wa);
      } else if (Date.now() - startedAt > timeoutMs) {
        clearInterval(timer);
        resolve(null);
      }
    }, 50);
  });
}

export function haptic(type: "success" | "error" | "warning" = "success"): void {
  getWebApp()?.HapticFeedback?.notificationOccurred(type);
}
