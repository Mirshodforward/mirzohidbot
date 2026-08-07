"use client";

/**
 * Asosiy UI bo'laklari.
 *
 * Barchasi semantik token klasslardan foydalanadi (`bg-surface`, `text-muted`,
 * `border-line`) — xom hex yo'q. Shu sababli yorug'/to'q rejim va Telegram
 * mavzusi avtomatik ishlaydi: bitta joyda o'zgartirilsa hamma joyda o'zgaradi.
 */

import { IconAlert, IconChevronRight } from "@/components/icons";

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl border border-line bg-surface p-4 ${className}`}>
      {children}
    </div>
  );
}

/** Sarlavha + qiymat qatori. Qiymat o'ngda, raqamlar bir xil kenglikda. */
export function Row({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: React.ReactNode;
  strong?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2">
      <span className="text-sm text-muted">{label}</span>
      <span
        className={`nums text-right text-sm ${strong ? "font-semibold" : "font-medium"}`}
      >
        {value}
      </span>
    </div>
  );
}

type Tone = "neutral" | "danger" | "success" | "warning";

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: Tone;
}) {
  const tones: Record<Tone, string> = {
    neutral: "bg-surface-2 text-muted",
    danger: "bg-danger/12 text-danger",
    success: "bg-success/12 text-success",
    warning: "bg-warning/15 text-warning",
  };
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-lg px-2 py-1 text-xs font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-surface-2 ${className}`} />;
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2.5 rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger"
    >
      <IconAlert size={18} className="mt-px shrink-0" />
      <span>{message}</span>
    </div>
  );
}

/**
 * Bo'sh holat. Baza yangi bo'lgani uchun bu foydalanuvchi ko'radigan
 * BIRINCHI ekran — shuning uchun u shunchaki "ma'lumot yo'q" demaydi,
 * balki keyingi qadamni aytadi.
 */
export function EmptyState({
  icon,
  title,
  body,
  action,
}: {
  icon?: React.ReactNode;
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-dashed border-line px-6 py-10 text-center">
      {icon && (
        <div className="mb-3 flex size-12 items-center justify-center rounded-full bg-surface-2 text-muted">
          {icon}
        </div>
      )}
      <p className="font-semibold">{title}</p>
      <p className="mt-1 max-w-xs text-sm text-muted">{body}</p>
      {action && <div className="mt-5 w-full max-w-xs">{action}</div>}
    </div>
  );
}

/** Sahifa sarlavhasi. Ixtiyoriy o'ng tomon (badge, tugma). */
export function PageTitle({
  children,
  right,
}: {
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h1 className="text-xl font-bold tracking-tight">{children}</h1>
      {right}
    </div>
  );
}

/** Bosiladigan ro'yxat qatori (sozlamalar, menyu). */
export function ListRow({
  icon,
  title,
  subtitle,
  onClick,
  danger = false,
}: {
  icon?: React.ReactNode;
  title: string;
  subtitle?: string;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex min-h-[56px] w-full cursor-pointer items-center gap-3 rounded-2xl border border-line bg-surface px-4 py-3 text-left transition-colors hover:bg-surface-2 ${
        danger ? "text-danger" : ""
      }`}
    >
      {icon && <span className="shrink-0 text-muted">{icon}</span>}
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium">{title}</span>
        {subtitle && <span className="mt-0.5 block text-xs text-muted">{subtitle}</span>}
      </span>
      <IconChevronRight size={18} className="shrink-0 text-muted" />
    </button>
  );
}
