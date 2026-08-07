"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { Badge, Card, ErrorBox, Row, Skeleton } from "@/components/ui";
import { useSession } from "@/components/SessionProvider";
import { StoreAdminActions } from "@/components/StoreAdminActions";
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
  // Next 15: `params` — Promise, `use()` bilan ochiladi.
  const { id } = use(params);
  const storeId = Number(id);

  const { me, loading: sessionLoading } = useSession();
  const [store, setStore] = useState<Store | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("umumiy");
  // Admin amali bajarilgach ma'lumotni qayta o'qish uchun hisoblagich.
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
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (error) return <ErrorBox message={error} />;
  if (!store) return null;

  const debt = store.debt_balance ?? 0;
  const left = daysUntil(store.next_payment_at);

  return (
    <div className="space-y-4">
      <Link href="/app" className="text-sm" style={{ color: "var(--tg-hint)" }}>
        ← Magazinlar
      </Link>

      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">{store.name}</h1>
          <p className="text-sm" style={{ color: "var(--tg-hint)" }}>
            {store.address ?? "—"}
          </p>
        </div>
        {debt > 0 ? <Badge tone="danger">Qarz bor</Badge> : <Badge tone="success">Toza</Badge>}
      </div>

      <nav
        className="flex gap-1 overflow-x-auto rounded-lg p-1"
        style={{ background: "var(--tg-card)" }}
      >
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => {
              setTab(t.id);
              haptic("success");
            }}
            className="flex-1 rounded-md px-3 py-2 text-sm font-medium whitespace-nowrap transition"
            style={
              tab === t.id
                ? { background: "var(--tg-accent)", color: "#fff" }
                : { color: "var(--tg-hint)" }
            }
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "umumiy" && (
        <Card>
          <Row label="Qarz" value={<strong>{sum(debt)}</strong>} />
          <Row label="Oylik (kelishuv)" value={sum(store.monthly_amount)} />
          <Row
            label="Keyingi to'lov"
            value={
              <>
                {date(store.next_payment_at)}
                {left !== null && left >= 0 && (
                  <span style={{ color: "var(--tg-hint)" }}> · {left} kun</span>
                )}
              </>
            }
          />
          <Row label="Hisobot sanasi" value={date(store.store_date)} />
          <Row
            label="Hisoblagich"
            value={store.electricity_kw !== null ? `${money(store.electricity_kw)} kW` : "—"}
          />
          <Row label="Oxirgi davr iste'moli" value={`${money(store.debt_tok)} kW`} />
          {store.electricity_price_per_kw !== null && (
            <>
              <Row label="Tok narxi" value={`${sum(store.electricity_price_per_kw)} / kW`} />
              <Row label="Tok uchun to'lash" value={sum(store.electricity_due)} />
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
      <Card>
        <p className="text-sm" style={{ color: "var(--tg-hint)" }}>
          Hozircha to'lov yozuvlari yo'q.
        </p>
      </Card>
    );

  return (
    <div className="space-y-2">
      {rows.map((p) => (
        <Card key={p.id}>
          <div className="flex items-baseline justify-between">
            <span className="font-medium text-emerald-600">− {sum(p.amount)}</span>
            <span className="text-xs" style={{ color: "var(--tg-hint)" }}>
              {dateTime(p.created_at)}
            </span>
          </div>
          <p className="mt-1 text-sm" style={{ color: "var(--tg-hint)" }}>
            Qoldiq: {sum(p.debt_after)}
          </p>
        </Card>
      ))}
    </div>
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
      <Card>
        <p className="text-sm" style={{ color: "var(--tg-hint)" }}>
          Hozircha hisoblagich yozuvlari yo'q.
        </p>
      </Card>
    );

  return (
    <div className="space-y-2">
      {rows.map((l) => (
        <Card key={l.id}>
          <div className="flex items-baseline justify-between">
            <span className="font-medium">+{money(l.delta_kw)} kW</span>
            <span className="text-xs" style={{ color: "var(--tg-hint)" }}>
              {date(l.period_from)} → {date(l.period_to)}
            </span>
          </div>
          <p className="mt-1 text-sm" style={{ color: "var(--tg-hint)" }}>
            {money(l.reading_before)} → {money(l.reading_after)} kW
          </p>
        </Card>
      ))}
    </div>
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

      {rows?.map((m) => (
        <div
          key={m.id}
          className={`max-w-[85%] rounded-xl px-3 py-2 ${m.from_admin ? "" : "ml-auto"}`}
          style={{
            background: m.from_admin ? "var(--tg-card)" : "var(--tg-accent)",
            color: m.from_admin ? "var(--tg-text)" : "#fff",
          }}
        >
          <p className="text-xs opacity-70">{m.from_admin ? "Admin" : "Magazin"}</p>
          <p className="mt-0.5 text-sm whitespace-pre-wrap">{m.body}</p>
          <p className="mt-1 text-[10px] opacity-60">{dateTime(m.created_at)}</p>
        </div>
      ))}

      {rows?.length === 0 && (
        <Card>
          <p className="text-sm" style={{ color: "var(--tg-hint)" }}>
            Hozircha yozishmalar yo'q.
          </p>
        </Card>
      )}

      <form onSubmit={send} className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Xabar yozing…"
          maxLength={4000}
          className="flex-1 rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-brand-500"
          style={{
            borderColor: "var(--tg-border)",
            background: "var(--tg-card)",
            color: "var(--tg-text)",
          }}
        />
        <button
          type="submit"
          disabled={busy || !text.trim()}
          className="rounded-lg px-4 py-2.5 text-sm font-medium text-white disabled:opacity-40"
          style={{ background: "var(--tg-accent)" }}
        >
          {busy ? "…" : "Yuborish"}
        </button>
      </form>

      {error && <ErrorBox message={error} />}
    </div>
  );
}
