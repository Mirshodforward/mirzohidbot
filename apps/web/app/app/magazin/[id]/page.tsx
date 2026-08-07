"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { StoreAdminActions } from "@/components/StoreAdminActions";
import { Button, Input } from "@/components/form";
import {
  IconArrowLeft,
  IconBolt,
  IconInbox,
  IconSend,
  IconWallet,
} from "@/components/icons";
import { Badge, Card, EmptyState, ErrorBox, Row, Skeleton } from "@/components/ui";
import {
  ApiError,
  api,
  type ChatMessage,
  type ElectricityLog,
  type Payment,
  type Store,
} from "@/lib/api";
import { date, dateTime, daysUntil, money, sum } from "@/lib/format";
import { haptic } from "@/lib/telegram";

type Tab = "umumiy" | "tolovlar" | "tok" | "suhbat" | "amallar";

const BASE_TABS: { id: Tab; label: string }[] = [
  { id: "umumiy", label: "Umumiy" },
  { id: "tolovlar", label: "To'lovlar" },
  { id: "tok", label: "Tok" },
  { id: "suhbat", label: "Suhbat" },
];

export default function StorePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const storeId = Number(id);

  const { me, loading: sessionLoading } = useSession();
  const [store, setStore] = useState<Store | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("umumiy");
  const [version, setVersion] = useState(0);

  const tabs = me?.is_admin
    ? [...BASE_TABS, { id: "amallar" as Tab, label: "Amallar" }]
    : BASE_TABS;

  useEffect(() => {
    if (!me || !Number.isFinite(storeId)) return;
    api
      .store(storeId)
      .then(setStore)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Magazin yuklanmadi."),
      );
  }, [me, storeId, version]);

  if (sessionLoading || (!store && !error)) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-5 w-28" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-52 w-full" />
      </div>
    );
  }
  if (error) return <ErrorBox message={error} />;
  if (!store) return null;

  const debt = store.debt_balance ?? 0;
  const left = daysUntil(store.next_payment_at);

  return (
    <div className="space-y-4">
      <Link
        href="/app"
        className="inline-flex min-h-[44px] cursor-pointer items-center gap-1.5 text-sm text-muted"
      >
        <IconArrowLeft size={18} />
        Magazinlar
      </Link>

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="truncate text-xl font-bold tracking-tight">{store.name}</h1>
          <p className="mt-0.5 truncate text-sm text-muted">{store.address ?? "—"}</p>
        </div>
        {debt > 0 ? <Badge tone="danger">Qarz bor</Badge> : <Badge tone="success">Toza</Badge>}
      </div>

      {/* Eng muhim raqam — birinchi ko'zga tashlanadi */}
      <Card className="bg-surface-2">
        <p className="text-xs text-muted">Joriy qarz</p>
        <p className={`nums mt-1 text-2xl font-bold ${debt > 0 ? "text-danger" : ""}`}>
          {sum(debt)}
        </p>
        {store.next_payment_at && (
          <p className="mt-1 text-xs text-muted">
            Keyingi to&apos;lov {date(store.next_payment_at)}
            {left !== null && left >= 0 && ` · ${left} kun qoldi`}
          </p>
        )}
      </Card>

      {/* Bo'limlar. Ko'p bo'lsa gorizontal siljiydi — sahifa emas, faqat shu qator */}
      <div
        role="tablist"
        aria-label="Magazin bo'limlari"
        className="-mx-1 flex gap-1 overflow-x-auto rounded-xl bg-surface p-1"
      >
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => {
              setTab(t.id);
              haptic("success");
            }}
            className={`min-h-[40px] flex-1 cursor-pointer rounded-lg px-3 text-sm font-medium whitespace-nowrap transition-colors ${
              tab === t.id ? "bg-primary text-on-primary" : "text-muted hover:text-text"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "umumiy" && (
        <Card>
          <Row label="Oylik (kelishuv)" value={sum(store.monthly_amount)} />
          <Row label="Hisobot sanasi" value={date(store.store_date)} />
          <Row
            label="Hisoblagich"
            value={store.electricity_kw !== null ? `${money(store.electricity_kw)} kW` : "—"}
          />
          <Row label="Oxirgi davr iste'moli" value={`${money(store.debt_tok)} kW`} />
          {store.electricity_price_per_kw !== null && (
            <>
              <Row label="Tok narxi" value={`${sum(store.electricity_price_per_kw)} / kW`} />
              <Row label="Tok uchun" value={sum(store.electricity_due)} strong />
            </>
          )}
          <Row label="Telefon" value={store.owner_phone ?? "—"} />
        </Card>
      )}

      {tab === "tolovlar" && <PaymentsTab storeId={storeId} key={`p${version}`} />}
      {tab === "tok" && <ElectricityTab storeId={storeId} key={`e${version}`} />}
      {tab === "suhbat" && <ChatTab storeId={storeId} />}
      {tab === "amallar" && me?.is_admin && (
        <StoreAdminActions store={store} onChanged={() => setVersion((v) => v + 1)} />
      )}
    </div>
  );
}

function PaymentsTab({ storeId }: { storeId: number }) {
  const [rows, setRows] = useState<Payment[] | null>(null);
  useEffect(() => {
    api.payments(storeId).then(setRows).catch(() => setRows([]));
  }, [storeId]);

  if (!rows) return <Skeleton className="h-24 w-full" />;
  if (rows.length === 0)
    return (
      <EmptyState
        icon={<IconWallet size={22} />}
        title="To'lov yo'q"
        body="Egasi to'lov qilganda admin uni shu yerda qayd etadi."
      />
    );

  return (
    <ul className="space-y-2">
      {rows.map((p) => (
        <li key={p.id}>
          <Card>
            <div className="flex items-baseline justify-between gap-3">
              <span className="nums font-semibold text-success">− {money(p.amount)}</span>
              <span className="nums text-xs text-muted">{dateTime(p.created_at)}</span>
            </div>
            <p className="nums mt-1 text-sm text-muted">Qoldiq: {sum(p.debt_after)}</p>
          </Card>
        </li>
      ))}
    </ul>
  );
}

function ElectricityTab({ storeId }: { storeId: number }) {
  const [rows, setRows] = useState<ElectricityLog[] | null>(null);
  useEffect(() => {
    api.electricity(storeId).then(setRows).catch(() => setRows([]));
  }, [storeId]);

  if (!rows) return <Skeleton className="h-24 w-full" />;
  if (rows.length === 0)
    return (
      <EmptyState
        icon={<IconBolt size={22} />}
        title="Hisoblagich yozuvi yo'q"
        body="Yangi ko'rsatkich kiritilganda davr va iste'mol shu yerda saqlanadi."
      />
    );

  return (
    <ul className="space-y-2">
      {rows.map((l) => (
        <li key={l.id}>
          <Card>
            <div className="flex items-baseline justify-between gap-3">
              <span className="nums font-semibold">+{money(l.delta_kw)} kW</span>
              <span className="nums text-xs text-muted">
                {date(l.period_from)} → {date(l.period_to)}
              </span>
            </div>
            <p className="nums mt-1 text-sm text-muted">
              {money(l.reading_before)} → {money(l.reading_after)} kW
            </p>
          </Card>
        </li>
      ))}
    </ul>
  );
}

function ChatTab({ storeId }: { storeId: number }) {
  const [rows, setRows] = useState<ChatMessage[] | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.messages(storeId).then(setRows).catch(() => setRows([]));
  }, [storeId]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const body = text.trim();
    if (!body) return;
    setBusy(true);
    setError(null);
    try {
      const msg = await api.sendMessage(storeId, body);
      setRows((prev) => [...(prev ?? []), msg]);
      setText("");
      haptic("success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Yuborilmadi.");
      haptic("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      {!rows && <Skeleton className="h-24 w-full" />}

      {rows?.length === 0 && (
        <EmptyState
          icon={<IconInbox size={22} />}
          title="Yozishmalar yo'q"
          body="Bu yerda yozilgan xabar Telegramga ham yetib boradi."
        />
      )}

      {rows && rows.length > 0 && (
        <ul className="space-y-2">
          {rows.map((m) => (
            <li
              key={m.id}
              className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 ${
                m.from_admin
                  ? "bg-surface"
                  : "ml-auto bg-primary text-on-primary"
              }`}
            >
              <p className="text-[11px] opacity-70">{m.from_admin ? "Admin" : "Magazin"}</p>
              <p className="mt-0.5 text-sm whitespace-pre-wrap">{m.body}</p>
              <p className="nums mt-1 text-[10px] opacity-60">{dateTime(m.created_at)}</p>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={send} className="flex items-end gap-2">
        <div className="flex-1">
          <Input
            label="Xabar"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Xabar yozing…"
            maxLength={4000}
          />
        </div>
        <Button
          type="submit"
          full={false}
          disabled={busy || !text.trim()}
          aria-label="Yuborish"
          className="mb-0 px-4"
          icon={<IconSend size={18} />}
        >
          <span className="sr-only">Yuborish</span>
        </Button>
      </form>

      {error && <ErrorBox message={error} />}
    </div>
  );
}
