import Link from "next/link";

import {
  IconBolt,
  IconCalendar,
  IconStore,
  IconWallet,
} from "@/components/icons";

const FEATURES = [
  {
    Icon: IconWallet,
    title: "Qarz avtomatik hisoblanadi",
    body: "Har 30 kunlik davr kelganda oylik summa qarzga o'zi qo'shiladi. Qo'lda hisoblash va unutilgan oylar yo'q.",
  },
  {
    Icon: IconCalendar,
    title: "Eslatma har kuni 09:00 da",
    body: "Qarzi bor magazin egasiga Telegramga eslatma boradi — Toshkent vaqti bilan aniq soatda, kuniga bir marta.",
  },
  {
    Icon: IconBolt,
    title: "Elektr hisoblagich tarixi",
    body: "Har o'qim davri saqlanadi: eski ko'rsatkich, yangi ko'rsatkich va iste'mol. Excel'ga yuklab olinadi.",
  },
  {
    Icon: IconStore,
    title: "Bot, Mini App va sayt",
    body: "Uchtasi bitta bazada ishlaydi. Botda kiritilgan to'lov saytda ham darhol ko'rinadi.",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-12 sm:py-20">
      <header className="flex items-center justify-between">
        <span className="text-lg font-bold tracking-tight">Mirzohid</span>
        <Link
          href="/kirish"
          className="inline-flex min-h-[44px] cursor-pointer items-center rounded-xl bg-primary px-5 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
        >
          Kirish
        </Link>
      </header>

      <section className="mt-16 sm:mt-24">
        <h1 className="max-w-2xl text-3xl font-bold tracking-tight text-balance sm:text-5xl">
          Magazin ijarasi, qarz va elektr hisobi — bitta joyda
        </h1>
        <p className="mt-5 max-w-xl text-base text-muted sm:text-lg">
          Ijaraga magazin beruvchilar uchun. Qarz o&apos;zi hisoblanadi, eslatma
          o&apos;z vaqtida boradi, hisobot Excel&apos;da tayyor turadi.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/kirish"
            className="inline-flex min-h-[48px] cursor-pointer items-center rounded-xl bg-primary px-6 text-sm font-semibold text-on-primary transition-opacity hover:opacity-90"
          >
            Kabinetga kirish
          </Link>
          <Link
            href="/app"
            className="inline-flex min-h-[48px] cursor-pointer items-center rounded-xl border border-line px-6 text-sm font-semibold transition-colors hover:bg-surface"
          >
            Mini App
          </Link>
        </div>
      </section>

      <section className="mt-20 grid gap-4 sm:mt-28 sm:grid-cols-2">
        {FEATURES.map(({ Icon, title, body }) => (
          <article key={title} className="rounded-2xl border border-line bg-surface p-6">
            <span className="inline-flex size-10 items-center justify-center rounded-xl bg-surface-2 text-primary">
              <Icon size={20} />
            </span>
            <h2 className="mt-3 font-semibold">{title}</h2>
            <p className="mt-1.5 text-sm leading-relaxed text-muted">{body}</p>
          </article>
        ))}
      </section>

      <footer className="mt-24 border-t border-line pt-8 text-sm text-muted">
        © {new Date().getFullYear()} Mirzohid
      </footer>
    </main>
  );
}
