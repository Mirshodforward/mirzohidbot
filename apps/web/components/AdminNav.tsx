"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Pastdagi navigatsiya — mobil ilovalardagidek.
 * Faqat admin ko'radi (`/app/admin/*` va `/app` bo'limlari).
 */

const ITEMS = [
  { href: "/app", label: "Magazinlar", icon: "🏪" },
  { href: "/app/admin", label: "Boshqaruv", icon: "📊" },
  { href: "/app/admin/xabar", label: "Xabar", icon: "✉️" },
  { href: "/app/admin/sozlamalar", label: "Sozlama", icon: "⚙️" },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav
      className="sticky bottom-0 -mx-4 mt-6 border-t px-2 pt-1 pb-[calc(0.25rem+env(safe-area-inset-bottom))]"
      style={{ background: "var(--tg-bg)", borderColor: "var(--tg-border)" }}
    >
      <ul className="flex">
        {ITEMS.map((item) => {
          // `/app` faqat aynan mos kelganda faol — aks holda hamma sahifada yonadi.
          const active =
            item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href);
          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                className="flex min-h-[52px] flex-col items-center justify-center gap-0.5 rounded-lg text-[11px] font-medium"
                style={{ color: active ? "var(--tg-accent)" : "var(--tg-hint)" }}
              >
                <span className="text-lg leading-none">{item.icon}</span>
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
