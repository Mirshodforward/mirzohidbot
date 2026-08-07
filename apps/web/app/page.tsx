import Link from "next/link";

const FEATURES = [
  {
    title: "Qarz avtomatik hisoblanadi",
    body: "Har 30 kunlik davr kelganda oylik summa qarzga o'zi qo'shiladi. Qo'lda hisoblash va unutilgan oylar yo'q.",
  },
  {
    title: "Eslatma har kuni 09:00 da",
    body: "Qarzi bor magazin egasiga Telegramga eslatma boradi — Toshkent vaqti bilan aniq soatda, kuniga bir marta.",
  },
  {
    title: "Elektr hisoblagich tarixi",
    body: "Har o'qim davri saqlanadi: eski ko'rsatkich, yangi ko'rsatkich va iste'mol. Excel'ga yuklab olinadi.",
  },
  {
    title: "Bot, Mini App va sayt",
    body: "Uchtasi bitta bazada ishlaydi. Botda kiritilgan to'lov saytda ham darhol ko'rinadi.",
  },
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-14 sm:py-20">
      <header className="flex items-center justify-between">
        <span className="text-lg font-semibold tracking-tight">Mirzohid</span>
        <Link
          href="/kirish"
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
        >
          Kirish
        </Link>
      </header>

      <section className="mt-16 sm:mt-24">
        <h1 className="max-w-2xl text-4xl font-bold tracking-tight text-balance sm:text-5xl">
          Magazin ijarasi, qarz va elektr hisobi — bitta joyda
        </h1>
        <p className="mt-5 max-w-xl text-lg" style={{ color: "var(--tg-hint)" }}>
          Ijaraga magazin beruvchilar uchun. Qarz o'zi hisoblanadi, eslatma o'z
          vaqtida boradi, hisobot Excel'da tayyor turadi.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/kirish"
            className="rounded-lg bg-brand-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            Kabinetga kirish
          </Link>
          <Link
            href="/app"
            className="rounded-lg border px-5 py-3 text-sm font-medium transition hover:bg-[var(--tg-card)]"
            style={{ borderColor: "var(--tg-border)" }}
          >
            Mini App
          </Link>
        </div>
      </section>

      <section className="mt-20 grid gap-5 sm:mt-28 sm:grid-cols-2">
        {FEATURES.map((f) => (
          <article
            key={f.title}
            className="rounded-xl border p-6"
            style={{ borderColor: "var(--tg-border)", background: "var(--tg-card)" }}
          >
            <h2 className="font-semibold">{f.title}</h2>
            <p className="mt-2 text-sm leading-relaxed" style={{ color: "var(--tg-hint)" }}>
              {f.body}
            </p>
          </article>
        ))}
      </section>

      <footer
        className="mt-24 border-t pt-8 text-sm"
        style={{ borderColor: "var(--tg-border)", color: "var(--tg-hint)" }}
      >
        © {new Date().getFullYear()} Mirzohid
      </footer>
    </main>
  );
}
