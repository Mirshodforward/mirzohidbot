"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Input, Notice } from "@/components/form";
import { IconArrowLeft } from "@/components/icons";
import { ApiError, api } from "@/lib/api";

type Step = "phone" | "code";

export default function LoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("+998");
  const [code, setCode] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submitPhone(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const out = await api.requestCode(phone);
      setNote(out.message);
      setStep("code");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xatolik yuz berdi.");
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.verifyCode(phone, code);
      router.push("/app");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xatolik yuz berdi.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-5 py-12">
      <Link
        href="/"
        className="inline-flex min-h-[44px] w-fit cursor-pointer items-center gap-1.5 text-sm text-muted"
      >
        <IconArrowLeft size={18} />
        Bosh sahifa
      </Link>

      <h1 className="mt-6 text-2xl font-bold tracking-tight">Kabinetga kirish</h1>
      <p className="mt-2 text-sm text-muted">
        {step === "phone"
          ? "Botga ulangan telefon raqamingizni kiriting — kirish kodi Telegramingizga yuboriladi."
          : "Telegramga kelgan 6 xonali kodni kiriting."}
      </p>

      {step === "phone" ? (
        <form onSubmit={submitPhone} className="mt-8 space-y-4">
          <Input
            label="Telefon raqam"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+998941339383"
            required
          />
          <Button type="submit" disabled={busy}>
            {busy ? "Yuborilmoqda…" : "Kod yuborish"}
          </Button>
        </form>
      ) : (
        <form onSubmit={submitCode} className="mt-8 space-y-4">
          <Input
            label="Kirish kodi"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            placeholder="123456"
            className="nums text-center text-2xl tracking-[0.4em]"
            required
            autoFocus
          />
          <Button type="submit" disabled={busy || code.length < 4}>
            {busy ? "Tekshirilmoqda…" : "Kirish"}
          </Button>
          <Button
            type="button"
            tone="neutral"
            onClick={() => {
              setStep("phone");
              setCode("");
              setError(null);
            }}
          >
            Raqamni o&apos;zgartirish
          </Button>
        </form>
      )}

      {note && step === "code" && <p className="mt-4 text-sm text-muted">{note}</p>}
      {error && (
        <div className="mt-4">
          <Notice tone="error">{error}</Notice>
        </div>
      )}
    </main>
  );
}
