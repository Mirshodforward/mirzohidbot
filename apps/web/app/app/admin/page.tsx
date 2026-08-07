"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button, Notice } from "@/components/form";
import {
  IconDownload,
  IconPlus,
  IconStore,
  IconUsers,
  IconWallet,
} from "@/components/icons";
import { Card, ErrorBox, PageTitle, Skeleton } from "@/components/ui";
import { ApiError, adminApi, type Stats } from "@/lib/api";
import { money } from "@/lib/format";

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

  if (loading) return <Skeleton className="h-56 w-full" />;
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
      <PageTitle>Boshqaruv</PageTitle>

      {error && <Notice tone="error">{error}</Notice>}

      {!stats ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <>
          {/* Asosiy raqam alohida, kattaroq — qolganlari ikkinchi darajali */}
          <Card className="bg-surface-2">
            <div className="flex items-center gap-2 text-muted">
              <IconWallet size={18} />
              <span className="text-xs">Jami qarz</span>
            </div>
            <p className="nums mt-1.5 text-3xl font-bold">{money(stats.total_debt)}</p>
            <p className="mt-1 text-xs text-muted">so&apos;m</p>
          </Card>

          <div className="grid grid-cols-3 gap-2.5">
            <Tile icon={<IconStore size={18} />} label="Magazin" value={stats.stores} />
            <Tile icon={<IconUsers size={18} />} label="Foydalanuvchi" value={stats.users} />
            <Tile
              icon={<IconUsers size={18} />}
              label="Kontakt ulagan"
              value={stats.linked_users}
            />
          </div>
        </>
      )}

      <Link href="/app/admin/yangi" className="block">
        <Button icon={<IconPlus size={18} />}>Yangi magazin qo&apos;shish</Button>
      </Link>

      <Card>
        <p className="mb-3 font-semibold">Hisobotlar</p>
        <div className="space-y-2">
          <Button
            tone="neutral"
            onClick={() => download("stores")}
            disabled={busy !== null}
            icon={<IconDownload size={18} />}
          >
            {busy === "stores" ? "Yuklanmoqda…" : "Magazinlar (Excel)"}
          </Button>
          <Button
            tone="neutral"
            onClick={() => download("full-report")}
            disabled={busy !== null}
            icon={<IconDownload size={18} />}
          >
            {busy === "full-report" ? "Yuklanmoqda…" : "To'liq hisobot (Excel)"}
          </Button>
        </div>
        <p className="mt-2.5 text-xs text-muted">
          To&apos;liq hisobot uch varaqdan iborat: magazinlar, qarzdan ayirishlar
          va tok tarixi.
        </p>
      </Card>

      <Card>
        <p className="mb-1 font-semibold">Eslatma jadvali</p>
        <p className="text-sm text-muted">
          Qarzi bor magazin egalariga har kuni soat <strong>09:00</strong> da
          (Toshkent vaqti) Telegramga eslatma boradi. Server o&apos;sha paytda
          o&apos;chiq bo&apos;lsa, ko&apos;tarilgach o&apos;sha kunning eslatmasi
          baribir yuboriladi.
        </p>
      </Card>
    </div>
  );
}

function Tile({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-3">
      <span className="text-muted">{icon}</span>
      <p className="nums mt-1.5 text-xl font-bold">{value}</p>
      <p className="mt-0.5 text-[11px] leading-tight text-muted">{label}</p>
    </div>
  );
}
