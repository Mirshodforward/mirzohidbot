"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useSession } from "@/components/SessionProvider";
import { Button } from "@/components/form";
import {
  IconChevronRight,
  IconPlus,
  IconStore,
} from "@/components/icons";
import { Badge, Card, EmptyState, ErrorBox, PageTitle, Skeleton } from "@/components/ui";
import { ApiError, api, type Store } from "@/lib/api";
import { date, daysUntil, money, sum } from "@/lib/format";

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
        <Skeleton className="h-8 w-44" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
      </div>
    );
  }

  if (sessionError) return <ErrorBox message={sessionError} />;
  if (error) return <ErrorBox message={error} />;

  const isAdmin = Boolean(me?.is_admin);
  const totalDebt = stores?.reduce((acc, s) => acc + (s.debt_balance ?? 0), 0) ?? 0;
  const indebted = stores?.filter((s) => (s.debt_balance ?? 0) > 0).length ?? 0;

  return (
    <div className="space-y-4">
      <PageTitle right={isAdmin ? <Badge tone="warning">Admin</Badge> : undefined}>
        {isAdmin ? "Magazinlar" : "Mening magazinlarim"}
      </PageTitle>

      {stores === null && <Skeleton className="h-28 w-full" />}

      {/* Jamlanma — ro'yxatga kirishdan oldin asosiy raqam ko'rinadi */}
      {stores && stores.length > 0 && (
        <Card className="bg-surface-2">
          <p className="text-xs text-muted">Jami qarz</p>
          <p className="nums mt-1 text-2xl font-bold">{sum(totalDebt)}</p>
          <p className="mt-1 text-xs text-muted">
            {stores.length} ta magazin
            {indebted > 0 && ` · ${indebted} tasida qarz bor`}
          </p>
        </Card>
      )}

      {stores?.length === 0 && (
        <EmptyState
          icon={<IconStore size={24} />}
          title={isAdmin ? "Hozircha magazin yo'q" : "Magazin topilmadi"}
          body={
            isAdmin
              ? "Birinchi magazinni qo'shing — keyin egasiga taklif havolasini yuborasiz."
              : "Telefon raqamingizga bog'langan magazin yo'q. Admin bilan bog'laning."
          }
          action={
            isAdmin ? (
              <Link href="/app/admin/yangi" className="block">
                <Button icon={<IconPlus size={18} />}>Magazin qo&apos;shish</Button>
              </Link>
            ) : undefined
          }
        />
      )}

      {stores && stores.length > 0 && (
        <ul className="space-y-2.5">
          {stores.map((s) => (
            <li key={s.id}>
              <StoreCard store={s} />
            </li>
          ))}
        </ul>
      )}

      {isAdmin && stores && stores.length > 0 && (
        <Link href="/app/admin/yangi" className="block">
          <Button tone="neutral" icon={<IconPlus size={18} />}>
            Yangi magazin
          </Button>
        </Link>
      )}
    </div>
  );
}

function StoreCard({ store }: { store: Store }) {
  const debt = store.debt_balance ?? 0;
  const left = daysUntil(store.next_payment_at);

  // Muddat yaqinlashgani ogohlantirish darajasini belgilaydi
  const tone = debt <= 0 ? "success" : left !== null && left <= 3 ? "danger" : "warning";
  const label = debt <= 0 ? "Qarz yo'q" : left !== null && left <= 3 ? "Muddat yaqin" : "Qarz bor";

  return (
    <Link
      href={`/app/magazin/${store.id}`}
      className="flex cursor-pointer items-center gap-3 rounded-2xl border border-line bg-surface p-4 transition-colors hover:bg-surface-2"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate font-semibold">{store.name}</p>
          <Badge tone={tone}>{label}</Badge>
        </div>
        <p className="mt-0.5 truncate text-xs text-muted">{store.address ?? "—"}</p>

        <div className="mt-3 flex items-baseline gap-4">
          <span>
            <span className="block text-[11px] text-muted">Qarz</span>
            <span className={`nums text-sm font-semibold ${debt > 0 ? "text-danger" : ""}`}>
              {money(debt)}
            </span>
          </span>
          <span>
            <span className="block text-[11px] text-muted">Keyingi to&apos;lov</span>
            <span className="nums text-sm font-medium">
              {date(store.next_payment_at)}
              {left !== null && left >= 0 && (
                <span className="text-muted"> · {left} kun</span>
              )}
            </span>
          </span>
        </div>
      </div>
      <IconChevronRight size={18} className="shrink-0 text-muted" />
    </Link>
  );
}
