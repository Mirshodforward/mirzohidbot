"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  IconDashboard,
  IconMessage,
  IconSettings,
  IconStore,
} from "@/components/icons";

/** Pastki navigatsiya. To'rt bo'lim — mobil uchun beshtadan oshmasligi kerak. */
const ITEMS = [
  { href: "/app", label: "Magazinlar", Icon: IconStore },
  { href: "/app/admin", label: "Boshqaruv", Icon: IconDashboard },
  { href: "/app/admin/xabar", label: "Xabar", Icon: IconMessage },
  { href: "/app/admin/sozlamalar", label: "Sozlama", Icon: IconSettings },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Asosiy bo'limlar"
      className="safe-b sticky bottom-0 -mx-4 mt-6 border-t border-line bg-bg/95 px-2 pt-1 backdrop-blur"
    >
      <ul className="flex">
        {ITEMS.map(({ href, label, Icon }) => {
          // `/app` faqat aynan mos kelganda faol — aks holda barcha
          // ichki sahifalarda ham yonib turadi.
          const active = href === "/app" ? pathname === "/app" : pathname.startsWith(href);
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex min-h-[54px] cursor-pointer flex-col items-center justify-center gap-1 rounded-xl text-[11px] font-medium transition-colors ${
                  active ? "text-primary" : "text-muted"
                }`}
              >
                <Icon size={21} />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
