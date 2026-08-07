"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button, NumberInput, Notice } from "@/components/form";
import { IconArrowLeft, IconCheck, IconLogout } from "@/components/icons";
import { Card, ErrorBox, Row, Skeleton } from "@/components/ui";
import { ApiError, adminApi, api, clearToken } from "@/lib/api";
import { money } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export default function SettingsPage() {
  const { me, loading, inTelegram } = useSession();
  const [price, setPrice] = useState<string>("");
  const [current, setCurrent] = useState<number | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!me?.is_admin) return;
    adminApi
      .getPrice()
      .then((r) => {
        setCurrent(r.price_per_kw);
        setPrice(r.price_per_kw === null ? "" : String(r.price_per_kw));
      })
      .catch(() => setCurrent(null));
  }, [me]);

  if (loading) return null;
  if (!me?.is_admin) return <ErrorBox message="Bu bo'lim faqat admin uchun." />;

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const out = await adminApi.setPrice(Number(price || "0"));
      setCurrent(out.price_per_kw);
      setSaved(true);
      haptic("success");
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Saqlanmadi.");
      haptic("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Link
        href="/app/admin"
        className="inline-flex min-h-[44px] cursor-pointer items-center gap-1.5 text-sm text-muted"
      >
        <IconArrowLeft size={18} />
        Boshqaruv
      </Link>
      <h1 className="text-xl font-bold tracking-tight">Sozlamalar</h1>

      <Card>
        <p className="mb-3 font-semibold">Tok narxi (hamma magazin uchun)</p>

        {current === undefined ? (
          <Skeleton className="h-12 w-full" />
        ) : (
          <>
            <p className="mb-3 text-sm text-muted">
              Hozirgi:{" "}
              <strong className="nums text-text">
                {current === null ? "kiritilmagan" : `${money(current)} so'm / kW`}
              </strong>
            </p>
            <NumberInput
              label="Yangi narx (so'm / kW)"
              value={price}
              onValueChange={setPrice}
              placeholder="1000"
              hint="0 — tok pullik hisoblanmaydi"
            />
            <div className="mt-3">
              <Button
                onClick={save}
                disabled={busy || price === ""}
                icon={saved ? <IconCheck size={18} /> : undefined}
              >
                {busy ? "Saqlanmoqda…" : saved ? "Saqlandi" : "Saqlash"}
              </Button>
            </div>
          </>
        )}
        {error && (
          <div className="mt-3">
            <Notice tone="error">{error}</Notice>
          </div>
        )}
      </Card>

      <Card>
        <p className="mb-1 font-semibold">Hisob</p>
        <Row label="Ism" value={me.full_name ?? "—"} />
        <Row label="Telefon" value={me.phone_number ?? "—"} />
        <Row label="Telegram ID" value={me.telegram_id ?? "—"} />
        <Row label="Rol" value="Admin" />
      </Card>

      {/* Mini App'da chiqish keraksiz — sessiyani Telegram boshqaradi */}
      {!inTelegram && (
        <Button
          tone="neutral"
          icon={<IconLogout size={18} />}
          onClick={async () => {
            try {
              await api.logout();
            } finally {
              clearToken();
              window.location.href = "/kirish";
            }
          }}
        >
          Chiqish
        </Button>
      )}
    </div>
  );
}
