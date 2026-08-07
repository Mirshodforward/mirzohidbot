"use client";

/**
 * Mobil uchun forma bo'laklari.
 *
 * Barcha input'larda `text-base` (16px) — iOS Safari undan kichik shriftli
 * maydonga fokus tushganda sahifani majburan kattalashtiradi.
 * Tegish maydonlari kamida 44px (Apple HIG minimumi).
 */

import { useId } from "react";

const FIELD_BASE =
  "w-full rounded-xl border px-4 py-3 text-base outline-none transition " +
  "focus:border-brand-500 disabled:opacity-50";

const fieldStyle = {
  borderColor: "var(--tg-border)",
  background: "var(--tg-bg)",
  color: "var(--tg-text)",
};

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium">{label}</span>
      {children}
      {hint && (
        <span className="mt-1 block text-xs" style={{ color: "var(--tg-hint)" }}>
          {hint}
        </span>
      )}
    </label>
  );
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export function Input({ label, hint, className = "", ...rest }: InputProps) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {label}
      </label>
      <input id={id} className={`${FIELD_BASE} ${className}`} style={fieldStyle} {...rest} />
      {hint && (
        <p className="mt-1 text-xs" style={{ color: "var(--tg-hint)" }}>
          {hint}
        </p>
      )}
    </div>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  hint?: string;
}

export function Textarea({ label, hint, className = "", ...rest }: TextareaProps) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {label}
      </label>
      <textarea
        id={id}
        className={`${FIELD_BASE} resize-y ${className}`}
        style={fieldStyle}
        {...rest}
      />
      {hint && (
        <p className="mt-1 text-xs" style={{ color: "var(--tg-hint)" }}>
          {hint}
        </p>
      )}
    </div>
  );
}

/** Raqamli maydon: mobil klaviatura raqamli ochiladi, faqat raqam qabul qiladi. */
export function NumberInput({
  label,
  hint,
  value,
  onValueChange,
  ...rest
}: {
  label: string;
  hint?: string;
  value: string;
  onValueChange: (v: string) => void;
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, "value" | "onChange">) {
  return (
    <Input
      label={label}
      hint={hint}
      type="text"
      inputMode="numeric"
      value={value}
      onChange={(e) => onValueChange(e.target.value.replace(/\D/g, ""))}
      {...rest}
    />
  );
}

type Tone = "primary" | "neutral" | "danger";

export function Button({
  tone = "primary",
  full = true,
  className = "",
  children,
  ...rest
}: {
  tone?: Tone;
  full?: boolean;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const base =
    "min-h-[44px] rounded-xl px-4 py-3 text-sm font-medium transition " +
    "active:scale-[0.98] disabled:opacity-40 disabled:active:scale-100";
  const width = full ? "w-full" : "";

  const styles: Record<Tone, React.CSSProperties> = {
    primary: { background: "var(--tg-accent)", color: "#fff" },
    neutral: {
      background: "var(--tg-card)",
      color: "var(--tg-text)",
      border: "1px solid var(--tg-border)",
    },
    danger: { background: "#dc2626", color: "#fff" },
  };

  return (
    <button className={`${base} ${width} ${className}`} style={styles[tone]} {...rest}>
      {children}
    </button>
  );
}

export function Notice({
  tone,
  children,
}: {
  tone: "ok" | "error";
  children: React.ReactNode;
}) {
  const cls =
    tone === "ok"
      ? "bg-emerald-500/10 text-emerald-600"
      : "bg-red-500/10 text-red-600";
  return <div className={`rounded-xl px-4 py-3 text-sm ${cls}`}>{children}</div>;
}
