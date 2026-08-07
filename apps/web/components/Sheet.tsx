"use client";

import { useEffect } from "react";

/**
 * Pastdan chiqadigan panel (bottom sheet).
 *
 * Mobil uchun modal oynadan qulayroq: barmoq ekranning pastki qismida
 * bo'ladi, kontent esa yuqorida ko'rinib turadi. Mini App'da ham,
 * brauzerda ham bir xil ishlaydi.
 */
export function Sheet({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  // Panel ochiq turganda orqadagi sahifa siljimasin.
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <button
        aria-label="Yopish"
        onClick={onClose}
        className="absolute inset-0 bg-black/50"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative max-h-[88dvh] w-full max-w-2xl overflow-y-auto rounded-t-2xl px-4 pt-3 pb-[calc(1rem+env(safe-area-inset-bottom))]"
        style={{ background: "var(--tg-bg)" }}
      >
        {/* Tortish chizig'i — bu panel pastdan chiqishini bildiradi */}
        <div
          className="mx-auto mb-3 h-1 w-10 rounded-full"
          style={{ background: "var(--tg-border)" }}
        />
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="min-h-[36px] min-w-[36px] rounded-lg text-xl leading-none"
            style={{ color: "var(--tg-hint)" }}
            aria-label="Yopish"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
