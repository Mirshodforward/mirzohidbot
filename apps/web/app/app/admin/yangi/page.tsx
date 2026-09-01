"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button, Input, NumberInput, Notice, Textarea } from "@/components/form";
import { IconArrowLeft, IconCheck, IconCopy } from "@/components/icons";
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

  // Telefon ixtiyoriy: bo'sh yoki hali to'ldirilmagan "+998" holati ham valid.
  const phoneDigits = phone.replace(/\s/g, "");
  const phoneEmpty = phoneDigits === "" || phoneDigits === "+998";
  const phoneTouched = !phoneEmpty;
  const phoneOk = phoneEmpty || /^\+998\d{9}$/.test(phoneDigits);
  const canSubmit =
    name.trim() !== "" && phoneOk && address.trim() !== "" && monthly !== "" && kw !== "";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const out = await adminApi.createStore({
        name: name.trim(),
        owner_phone: phoneEmpty ? undefined : phoneDigits,
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

  // --- Yaratilgandan keyin: taklif havolasi ---
  if (created) {
    const link = created.invite_link;
    return (
      <div className="space-y-4">
        <Notice tone="ok">Magazin yaratildi: {created.store.name}</Notice>

        <Card>
          <p className="font-semibold">Egasiga havola</p>
          <p className="mt-1 mb-3 text-sm text-muted">
            {created.store.owner_phone ? (
              <>
                Havolani magazin egasiga yuboring. U bosganda bot ochiladi va
                kontaktini ulashadi — raqam siz kiritgan{" "}
                <span className="nums text-text">{created.store.owner_phone}</span>{" "}
                bilan mos kelishi kerak (mos kelmasa ham, havola orqali
                raqamsiz ulanish tugmasi chiqadi).
              </>
            ) : (
              <>
                Telefon kiritilmagan. Havolani magazin egasiga yuboring — u
                bosgan zahoti (hech narsa so&apos;ralmasdan) shu magazinga
                bog&apos;lanadi.
              </>
            )}
          </p>

          {link ? (
            <>
              <div className="mb-3 overflow-x-auto rounded-xl border border-line bg-bg px-3 py-2.5 text-xs">
                <code className="whitespace-nowrap">{link}</code>
              </div>
              <Button
                icon={copied ? <IconCheck size={18} /> : <IconCopy size={18} />}
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
                {copied ? "Nusxa olindi" : "Havoladan nusxa olish"}
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
          <Button
            tone="neutral"
            onClick={() => router.push(`/app/magazin/${created.store.id}`)}
          >
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

  return (
    <div className="space-y-4">
      <Link
        href="/app/admin"
        className="inline-flex min-h-[44px] cursor-pointer items-center gap-1.5 text-sm text-muted"
      >
        <IconArrowLeft size={18} />
        Boshqaruv
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
          label="Egasining telefoni (ixtiyoriy)"
          type="tel"
          inputMode="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+998941339383"
          invalid={phoneTouched && !phoneOk}
          hint={
            phoneTouched && !phoneOk
              ? "Format: +998 va 9 ta raqam"
              : "Bo'sh qoldirsangiz ham bo'ladi — egasi taklif havolasi (=magazin ID) orqali to'g'ridan-to'g'ri bog'lanadi"
          }
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
          hint="Elektr hisoblagichning hozirgi raqami"
          required
        />

        <Textarea
          label="Izoh (ixtiyoriy)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
        />

        <Card>
          <p className="text-sm text-muted">
            Magazin yaratilganda <strong className="text-text">birinchi oylik</strong>{" "}
            darhol qarzga yoziladi, keyingilari har 30 kunda avtomatik qo&apos;shiladi.
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
