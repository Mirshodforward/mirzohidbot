"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button, Notice } from "@/components/form";
import { Card, ErrorBox, Skeleton } from "@/components/ui";
import { ApiError, adminApi, type Stats } from "@/lib/api";
import { sum } from "@/lib/format";

export default function AdminDashboard() {
  const { me, loading } = useSession();
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    if (!me?.is_admin) return;
    adminApi
      .stats()
      .then(setStats)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Statistika yuklanmadi."),
      );
  }, [me]);

  if (loading) return <Skeleton className="h-48 w-full" />;
  if (!me?.is_admin) {
    return (
      <ErrorBox message="Bu bo'lim faqat admin uchun. Agar admin bo'lsangiz, ADMIN_IDS ro'yxatida Telegram ID'ingiz borligini tekshiring." />
    );
  }

  async function download(kind: "stores" | "full-report") {
    setBusy(kind);
    setError(null);
    try {
      await adminApi.downloadExcel(kind);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Fayl yuklanmadi.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold tracking-tight">Boshqaruv</h1>

      {error && <Notice tone="error">{error}</Notice>}

      {!stats ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <StatTile label="Magazinlar" value={String(stats.stores)} />
          <StatTile label="Foydalanuvchilar" value={String(stats.users)} />
          <StatTile label="Kontakt ulaganlar" value={String(stats.linked_users)} />
          <StatTile label="Jami qarz" value={sum(stats.total_debt)} accent />
        </div>
      )}

      <Link href="/app/admin/yangi" className="block">
        <Button>➕ Yangi magazin qo&apos;shish</Button>
      </Link>

      <Card>
        <p className="mb-3 font-medium">Hisobotlar</p>
        <div className="space-y-2">
          <Button
            tone="neutral"
            onClick={() => download("stores")}
            disabled={busy !== null}
          >
            {busy === "stores" ? "Yuklanmoqda…" : "📊 Magazinlar (Excel)"}
          </Button>
          <Button
            tone="neutral"
            onClick={() => download("full-report")}
            disabled={busy !== null}
          >
            {busy === "full-report" ? "Yuklanmoqda…" : "📋 To'liq hisobot (Excel)"}
          </Button>
        </div>
        <p className="mt-2 text-xs" style={{ color: "var(--tg-hint)" }}>
          To&apos;liq hisobot: magazinlar + qarzdan ayirishlar + tok tarixi.
        </p>
      </Card>

      <Card>
        <p className="mb-1 font-medium">Eslatma jadvali</p>
        <p className="text-sm" style={{ color: "var(--tg-hint)" }}>
          Qarzi bor magazin egalariga har kuni <strong>09:00</strong> da (Toshkent
          vaqti) Telegramga eslatma boradi. Server o&apos;sha paytda o&apos;chiq
          bo&apos;lsa, ko&apos;tarilgach o&apos;sha kunning eslatmasi baribir yuboriladi.
        </p>
      </Card>
    </div>
  );
}

function StatTile({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      className="rounded-xl border p-4"
      style={{ borderColor: "var(--tg-border)", background: "var(--tg-card)" }}
    >
      <p className="text-xs" style={{ color: "var(--tg-hint)" }}>
        {label}
      </p>
      <p
        className="mt-1 text-lg font-bold tabular-nums"
        style={accent ? { color: "#dc2626" } : undefined}
      >
        {value}
      </p>
    </div>
  );
}
