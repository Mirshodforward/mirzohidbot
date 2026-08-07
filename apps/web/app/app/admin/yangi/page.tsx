"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button, Input, NumberInput, Notice, Textarea } from "@/components/form";
import { Card, ErrorBox } from "@/components/ui";
import { ApiError, adminApi, type StoreCreated } from "@/lib/api";
import { money } from "@/lib/format";
import { haptic } from "@/lib/telegram";

export default function NewStorePage() {
  const router = useRouter();
  const { me, loading } = useSession();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+998");
  const [address, setAddress] = useState("");
  const [monthly, setMonthly] = useState("");
  const [kw, setKw] = useState("");
  const [description, setDescription] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<StoreCreated | null>(null);
  const [copied, setCopied] = useState(false);

  if (loading) return null;
  if (!me?.is_admin) return <ErrorBox message="Bu bo'lim faqat admin uchun." />;

  const phoneOk = /^\+998\d{9}$/.test(phone.replace(/\s/g, ""));
  const canSubmit =
    name.trim() !== "" && phoneOk && address.trim() !== "" && monthly !== "" && kw !== "";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const out = await adminApi.createStore({
        name: name.trim(),
        owner_phone: phone.replace(/\s/g, ""),
        address: address.trim(),
        monthly_amount: Number(monthly),
        electricity_kw: Number(kw),
        description: description.trim() || null,
      });
      setCreated(out);
      haptic("success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Magazin yaratilmadi.");
      haptic("error");
    } finally {
      setBusy(false);
    }
  }

  // --- Yaratilgandan keyingi ekran: taklif havolasi ---
  if (created) {
    const link = created.invite_link;
    return (
      <div className="space-y-4">
        <Notice tone="ok">✅ Magazin yaratildi: {created.store.name}</Notice>

        <Card>
          <p className="font-medium">Egasiga havola</p>
          <p className="mt-1 mb-3 text-sm" style={{ color: "var(--tg-hint)" }}>
            Shu havolani magazin egasiga yuboring. U bosganda bot ochiladi va
            kontaktini ulashadi — raqam siz kiritgan{" "}
            <code className="text-xs">{created.store.owner_phone}</code> bilan mos
            kelishi kerak.
          </p>

          {link ? (
            <>
              <div
                className="mb-3 overflow-x-auto rounded-lg border px-3 py-2.5 text-xs"
                style={{ borderColor: "var(--tg-border)", background: "var(--tg-card)" }}
              >
                <code className="whitespace-nowrap">{link}</code>
              </div>
              <Button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(link);
                    setCopied(true);
                    haptic("success");
                    setTimeout(() => setCopied(false), 2000);
                  } catch {
                    setError("Nusxa olinmadi — havolani qo'lda belgilab oling.");
                  }
                }}
              >
                {copied ? "✓ Nusxa olindi" : "📋 Havoladan nusxa olish"}
              </Button>
            </>
          ) : (
            <Notice tone="error">
              Botda @username yo&apos;q — havola yaratilmadi. Egasi qo&apos;lda
              yuborsin: <code>/start {created.invite_token}</code>
            </Notice>
          )}
        </Card>

        <div className="space-y-2">
          <Button tone="neutral" onClick={() => router.push(`/app/magazin/${created.store.id}`)}>
            Magazinni ochish
          </Button>
          <Button
            tone="neutral"
            onClick={() => {
              setCreated(null);
              setName("");
              setPhone("+998");
              setAddress("");
              setMonthly("");
              setKw("");
              setDescription("");
            }}
          >
            Yana bitta qo&apos;shish
          </Button>
        </div>
      </div>
    );
  }

  // --- Forma ---
  return (
    <div className="space-y-4">
      <Link href="/app/admin" className="text-sm" style={{ color: "var(--tg-hint)" }}>
        ← Boshqaruv
      </Link>
      <h1 className="text-xl font-bold tracking-tight">Yangi magazin</h1>

      <form onSubmit={submit} className="space-y-4">
        <Input
          label="Magazin nomi"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Masalan: Do'kon №5"
          required
        />

        <Input
          label="Egasining telefoni"
          type="tel"
          inputMode="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+998941339383"
          hint={
            phone.length > 4 && !phoneOk
              ? "⚠️ Format: +998 va 9 ta raqam"
              : "Egasi aynan shu raqamli kontaktni yuborishi kerak"
          }
          required
        />

        <Input
          label="Manzil"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Ko'cha, bino"
          required
        />

        <NumberInput
          label="Oylik summa (so'm)"
          value={monthly}
          onValueChange={setMonthly}
          placeholder="5000000"
          hint={monthly ? `${money(Number(monthly))} so'm` : "Kelishilgan oylik ijara"}
          required
        />

        <NumberInput
          label="Hisoblagich ko'rsatkichi (kW)"
          value={kw}
          onValueChange={setKw}
          placeholder="4197"
          hint="Hozirgi elektr hisoblagich raqami"
          required
        />

        <Textarea
          label="Izoh (ixtiyoriy)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
        />

        <Card>
          <p className="text-sm" style={{ color: "var(--tg-hint)" }}>
            Magazin yaratilganda <strong>birinchi oylik</strong> darhol qarzga
            yoziladi, keyingilari esa har 30 kunda avtomatik qo&apos;shiladi.
          </p>
        </Card>

        {error && <Notice tone="error">{error}</Notice>}

        <Button type="submit" disabled={busy || !canSubmit}>
          {busy ? "Yaratilmoqda…" : "Magazin yaratish"}
        </Button>
      </form>
    </div>
  );
}
