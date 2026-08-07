"use client";

/** Kichik, umumiy UI bo'laklari. shadcn/ui keyin ustiga qo'shilishi mumkin. */

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border p-4 ${className}`}
      style={{ borderColor: "var(--tg-border)", background: "var(--tg-card)" }}
    >
      {children}
    </div>
  );
}

export function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <span className="text-sm" style={{ color: "var(--tg-hint)" }}>
        {label}
      </span>
      <span className="text-right text-sm font-medium tabular-nums">{value}</span>
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "danger" | "success" | "warning";
}) {
  const tones: Record<string, string> = {
    neutral: "bg-slate-500/12 text-slate-600",
    danger: "bg-red-500/12 text-red-600",
    success: "bg-emerald-500/12 text-emerald-600",
    warning: "bg-amber-500/15 text-amber-700",
  };
  return (
    <span
      className={`inline-flex rounded-md px-2 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg ${className}`}
      style={{ background: "var(--tg-border)" }}
    />
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-600">{message}</div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <Card className="text-center">
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-sm" style={{ color: "var(--tg-hint)" }}>
        {body}
      </p>
    </Card>
  );
}
