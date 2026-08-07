"use client";

/**
 * Forma bo'laklari.
 *
 * Mobil qoidalar (UI/UX tekshiruvidan):
 *  - input shrifti 16px (`text-base`) — iOS undan kichigida sahifani
 *    majburan kattalashtiradi va foydalanuvchi qo'lda qaytarishga majbur;
 *  - tegish maydoni kamida 44px;
 *  - raqamlar uchun `inputMode` — mobil klaviatura raqamli ochiladi;
 *  - yorliq har doim ko'rinadi (placeholder yorliq o'rnini bosmaydi —
 *    yozishni boshlagach u yo'qoladi va maydon nima ekani unutiladi).
 */

import { useId } from "react";

import { IconAlert, IconCheck } from "@/components/icons";

const FIELD =
  "w-full rounded-xl border border-line bg-bg px-4 py-3 text-base text-text " +
  "outline-none transition-colors placeholder:text-muted/60 " +
  "focus:border-primary disabled:opacity-50";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  invalid?: boolean;
}

export function Input({ label, hint, invalid, className = "", ...rest }: InputProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {label}
      </label>
      <input
        id={id}
        aria-describedby={hint ? hintId : undefined}
        aria-invalid={invalid || undefined}
        className={`${FIELD} ${invalid ? "border-danger" : ""} ${className}`}
        {...rest}
      />
      {hint && (
        <p id={hintId} className={`mt-1.5 text-xs ${invalid ? "text-danger" : "text-muted"}`}>
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
      <textarea id={id} className={`${FIELD} resize-y ${className}`} {...rest} />
      {hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function NumberInput({
  value,
  onValueChange,
  ...rest
}: {
  value: string;
  onValueChange: (v: string) => void;
} & Omit<InputProps, "value" | "onChange" | "type">) {
  return (
    <Input
      type="text"
      inputMode="numeric"
      autoComplete="off"
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
  icon,
  className = "",
  children,
  ...rest
}: {
  tone?: Tone;
  full?: boolean;
  icon?: React.ReactNode;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const tones: Record<Tone, string> = {
    primary: "bg-primary text-on-primary hover:opacity-90",
    neutral: "bg-surface text-text border border-line hover:bg-surface-2",
    danger: "bg-danger text-white hover:opacity-90",
  };
  return (
    <button
      className={
        "inline-flex min-h-[48px] cursor-pointer items-center justify-center gap-2 " +
        "rounded-xl px-4 py-3 text-sm font-semibold transition-opacity " +
        // Bosilganda faqat opacity/rang o'zgaradi — o'lcham o'zgarsa
        // atrofdagi kontent sakraydi.
        "active:opacity-80 disabled:cursor-not-allowed disabled:opacity-40 " +
        `${full ? "w-full" : ""} ${tones[tone]} ${className}`
      }
      {...rest}
    >
      {icon}
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
  const ok = tone === "ok";
  return (
    <div
      role={ok ? "status" : "alert"}
      className={`flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm ${
        ok ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
      }`}
    >
      {ok ? (
        <IconCheck size={18} className="mt-px shrink-0" />
      ) : (
        <IconAlert size={18} className="mt-px shrink-0" />
      )}
      <span className="min-w-0">{children}</span>
    </div>
  );
}
