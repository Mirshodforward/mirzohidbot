"use client";

import Link from "next/link";
import { useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button, Notice, Textarea } from "@/components/form";
import { IconArrowLeft, IconSend } from "@/components/icons";
import { Card, ErrorBox } from "@/components/ui";
import { ApiError, adminApi } from "@/lib/api";
import { haptic } from "@/lib/telegram";

export default function BroadcastPage() {
  const { me, loading } = useSession();
  const [text, setText] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    sent: number;
    blocked: number;
    failed: number;
  } | null>(null);

  if (loading) return null;
  if (!me?.is_admin) return <ErrorBox message="Bu bo'lim faqat admin uchun." />;

  async function send() {
    setBusy(true);
    setError(null);
    try {
      const out = await adminApi.broadcast(text.trim());
      setResult(out);
      setText("");
      setConfirming(false);
      haptic("success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Yuborilmadi.");
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
      <h1 className="text-xl font-bold tracking-tight">Barchaga xabar</h1>

      <Card>
        <p className="text-sm text-muted">
          Xabar <strong className="text-text">kontakt ulagan barcha
          foydalanuvchilarga</strong> Telegram orqali yuboriladi. Yuborilgandan
          keyin qaytarib bo&apos;lmaydi.
        </p>
      </Card>

      <Textarea
        label="Xabar matni"
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setConfirming(false);
          setResult(null);
        }}
        rows={6}
        maxLength={4000}
        placeholder="Assalomu alaykum…"
        hint={`${text.length} / 4000`}
      />

      {error && <Notice tone="error">{error}</Notice>}

      {result && (
        <Notice tone="ok">
          Yuborildi: <strong>{result.sent}</strong>
          {result.blocked > 0 && ` · Botni bloklaganlar: ${result.blocked}`}
          {result.failed > 0 && ` · Xato: ${result.failed}`}
        </Notice>
      )}

      {/* Ikki bosqich — tasodifan yuborib yubormaslik uchun */}
      {!confirming ? (
        <Button
          disabled={!text.trim() || busy}
          onClick={() => setConfirming(true)}
          icon={<IconSend size={18} />}
        >
          Yuborishga tayyorlash
        </Button>
      ) : (
        <div className="space-y-2">
          <Notice tone="error">
            Bu xabar hamma foydalanuvchilarga ketadi. Tasdiqlaysizmi?
          </Notice>
          <Button tone="danger" disabled={busy} onClick={send}>
            {busy ? "Yuborilmoqda…" : "Ha, yuborish"}
          </Button>
          <Button tone="neutral" disabled={busy} onClick={() => setConfirming(false)}>
            Bekor qilish
          </Button>
        </div>
      )}
    </div>
  );
}
