"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

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

  const inputClass =
    "w-full rounded-lg border px-4 py-3 text-base outline-none focus:border-brand-500";
  const inputStyle = {
    borderColor: "var(--tg-border)",
    background: "var(--tg-card)",
    color: "var(--tg-text)",
  };

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-5 py-12">
      <Link href="/" className="text-sm" style={{ color: "var(--tg-hint)" }}>
        ← Bosh sahifa
      </Link>

      <h1 className="mt-8 text-2xl font-bold tracking-tight">Kabinetga kirish</h1>
      <p className="mt-2 text-sm" style={{ color: "var(--tg-hint)" }}>
        {step === "phone"
          ? "Botga ulangan telefon raqamingizni kiriting — kirish kodi Telegramingizga yuboriladi."
          : "Telegramga kelgan 6 xonali kodni kiriting."}
      </p>

      {step === "phone" ? (
        <form onSubmit={submitPhone} className="mt-8 space-y-4">
          <input
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+998941339383"
            className={inputClass}
            style={inputStyle}
            required
          />
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-brand-600 py-3 font-medium text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? "Yuborilmoqda…" : "Kod yuborish"}
          </button>
        </form>
      ) : (
        <form onSubmit={submitCode} className="mt-8 space-y-4">
          <input
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            placeholder="123456"
            className={`${inputClass} text-center text-2xl tracking-[0.5em]`}
            style={inputStyle}
            required
            autoFocus
          />
          <button
            type="submit"
            disabled={busy || code.length < 4}
            className="w-full rounded-lg bg-brand-600 py-3 font-medium text-white transition hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? "Tekshirilmoqda…" : "Kirish"}
          </button>
          <button
            type="button"
            onClick={() => {
              setStep("phone");
              setCode("");
              setError(null);
            }}
            className="w-full py-2 text-sm"
            style={{ color: "var(--tg-hint)" }}
          >
            Raqamni o'zgartirish
          </button>
        </form>
      )}

      {note && step === "code" && (
        <p className="mt-4 text-sm" style={{ color: "var(--tg-hint)" }}>
          {note}
        </p>
      )}
      {error && (
        <p className="mt-4 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </main>
  );
}
