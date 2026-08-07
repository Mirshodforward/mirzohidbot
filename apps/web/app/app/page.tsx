"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge, Card, ErrorBox, EmptyState, Row, Skeleton } from "@/components/ui";
import { useSession } from "@/components/SessionProvider";
import { ApiError, api, type Store } from "@/lib/api";
import { date, daysUntil, sum } from "@/lib/format";

export default function StoresPage() {
  const { me, loading: sessionLoading, error: sessionError } = useSession();
  const [stores, setStores] = useState<Store[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!me) return;
    api
      .stores()
      .then(setStores)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Ma'lumot yuklanmadi."),
      );
  }, [me]);

  if (sessionLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (sessionError) return <ErrorBox message={sessionError} />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div className="space-y-4">
      <header className="flex items-baseline justify-between">
        <h1 className="text-xl font-bold tracking-tight">
          {me?.is_admin ? "Barcha magazinlar" : "Mening magazinlarim"}
        </h1>
        {me?.is_admin && <Badge tone="warning">Admin</Badge>}
      </header>

      {stores === null && <Skeleton className="h-32 w-full" />}

      {stores?.length === 0 && (
        <EmptyState
          title="Magazin topilmadi"
          body="Telefon raqamingizga bog'langan magazin yo'q. Admin bilan bog'laning."
        />
      )}

      {stores?.map((s) => (
        <StoreCard key={s.id} store={s} />
      ))}
    </div>
  );
}

function StoreCard({ store }: { store: Store }) {
  const debt = store.debt_balance ?? 0;
  const left = daysUntil(store.next_payment_at);

  return (
    <Link href={`/app/magazin/${store.id}`} className="block">
      <Card className="transition active:scale-[0.99]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-semibold">{store.name}</p>
            <p className="mt-0.5 text-sm" style={{ color: "var(--tg-hint)" }}>
              {store.address ?? "—"}
            </p>
          </div>
          {debt > 0 ? (
            <Badge tone="danger">Qarz bor</Badge>
          ) : (
            <Badge tone="success">Qarz yo'q</Badge>
          )}
        </div>

        <div className="mt-3 border-t pt-2" style={{ borderColor: "var(--tg-border)" }}>
          <Row label="Qarz" value={sum(debt)} />
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
          {store.electricity_due !== null && (
            <Row label="Tok (oxirgi davr)" value={sum(store.electricity_due)} />
          )}
        </div>
      </Card>
    </Link>
  );
}
