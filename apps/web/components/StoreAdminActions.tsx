"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Sheet } from "@/components/Sheet";
import { Button, Input, NumberInput, Notice } from "@/components/form";
import {
  IconBolt,
  IconCheck,
  IconCopy,
  IconLink,
  IconMinus,
  IconPencil,
  IconTrash,
} from "@/components/icons";
import { Card } from "@/components/ui";
import { ApiError, adminApi, type Store } from "@/lib/api";
import { money, sum } from "@/lib/format";
import { haptic } from "@/lib/telegram";

type Panel = "payment" | "reading" | "edit" | "invite" | "delete" | null;

export function StoreAdminActions({
  store,
  onChanged,
}: {
  store: Store;
  onChanged: () => void;
}) {
  const [panel, setPanel] = useState<Panel>(null);

  return (
    <>
      <div className="space-y-2">
        <Button onClick={() => setPanel("payment")} icon={<IconMinus size={18} />}>
          To&apos;lov qabul qilish
        </Button>
        <Button
          tone="neutral"
          onClick={() => setPanel("reading")}
          icon={<IconBolt size={18} />}
        >
          Yangi hisoblagich ko&apos;rsatkichi
        </Button>
        <Button
          tone="neutral"
          onClick={() => setPanel("edit")}
          icon={<IconPencil size={18} />}
        >
          Ma&apos;lumotlarni tahrirlash
        </Button>
        <Button
          tone="neutral"
          onClick={() => setPanel("invite")}
          icon={<IconLink size={18} />}
        >
          Yangi taklif havolasi
        </Button>
        <Button
          tone="danger"
          onClick={() => setPanel("delete")}
          icon={<IconTrash size={18} />}
        >
          Magazinni o&apos;chirish
        </Button>
      </div>

      <PaymentPanel
        store={store}
        open={panel === "payment"}
        close={() => setPanel(null)}
        onDone={onChanged}
      />
      <ReadingPanel
        store={store}
        open={panel === "reading"}
        close={() => setPanel(null)}
        onDone={onChanged}
      />
      <EditPanel
        store={store}
        open={panel === "edit"}
        close={() => setPanel(null)}
        onDone={onChanged}
      />
      <InvitePanel store={store} open={panel === "invite"} close={() => setPanel(null)} />
      <DeletePanel store={store} open={panel === "delete"} close={() => setPanel(null)} />
    </>
  );
}

function useAction(close: () => void, onDone?: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      haptic("success");
      onDone?.();
      close();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Amal bajarilmadi.");
      haptic("error");
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, setError, run };
}

function PaymentPanel({
  store,
  open,
  close,
  onDone,
}: {
  store: Store;
  open: boolean;
  close: () => void;
  onDone: () => void;
}) {
  const [amount, setAmount] = useState("");
  const { busy, error, run } = useAction(close, onDone);
  const debt = store.debt_balance ?? 0;
  const value = Number(amount || "0");

  return (
    <Sheet open={open} onClose={close} title="To'lov qabul qilish">
      <div className="space-y-4">
        <Card>
          <p className="text-sm text-muted">
            Hozirgi qarz: <strong className="nums text-text">{sum(debt)}</strong>
          </p>
        </Card>

        <NumberInput
          label="Egasi bergan summa (so'm)"
          value={amount}
          onValueChange={setAmount}
          placeholder="500000"
          autoFocus
          hint={
            value > debt
              ? `⚠️ Qarzdan ko'p — faqat ${money(debt)} so'm ayiriladi`
              : value > 0
                ? `Qoladi: ${money(debt - value)} so'm`
                : undefined
          }
        />

        {error && <Notice tone="error">{error}</Notice>}

        <Button
          disabled={busy || value <= 0 || debt <= 0}
          onClick={() => run(async () => void (await adminApi.addPayment(store.id, value)))}
        >
          {busy ? "Saqlanmoqda…" : "Qarzdan ayirish"}
        </Button>
      </div>
    </Sheet>
  );
}

function ReadingPanel({
  store,
  open,
  close,
  onDone,
}: {
  store: Store;
  open: boolean;
  close: () => void;
  onDone: () => void;
}) {
  const [reading, setReading] = useState("");
  const { busy, error, run } = useAction(close, onDone);
  const prev = store.electricity_kw;
  const value = Number(reading || "0");
  const delta = prev !== null && value >= prev ? value - prev : null;
  const price = store.electricity_price_per_kw;

  return (
    <Sheet open={open} onClose={close} title="Hisoblagich ko'rsatkichi">
      <div className="space-y-4">
        <Card>
          <p className="text-sm text-muted">
            Oxirgi ko&apos;rsatkich:{" "}
            <strong className="nums text-text">
              {prev !== null ? `${money(prev)} kW` : "kiritilmagan"}
            </strong>
          </p>
        </Card>

        <NumberInput
          label="Yangi ko'rsatkich (kW)"
          value={reading}
          onValueChange={setReading}
          placeholder={prev !== null ? String(prev + 100) : "4197"}
          autoFocus
          hint={
            prev !== null && reading !== "" && value < prev
              ? "Oldingisidan kichik — hisoblagich orqaga qaytmaydi"
              : delta !== null
                ? `Iste'mol: ${money(delta)} kW` +
                  (price !== null ? ` = ${money(delta * price)} so'm` : "")
                : undefined
          }
        />

        {error && <Notice tone="error">{error}</Notice>}

        <Button
          disabled={busy || reading === "" || (prev !== null && value < prev)}
          onClick={() => run(async () => void (await adminApi.addReading(store.id, value)))}
        >
          {busy ? "Saqlanmoqda…" : "Saqlash"}
        </Button>
      </div>
    </Sheet>
  );
}

function EditPanel({
  store,
  open,
  close,
  onDone,
}: {
  store: Store;
  open: boolean;
  close: () => void;
  onDone: () => void;
}) {
  const [name, setName] = useState(store.name);
  const [address, setAddress] = useState(store.address ?? "");
  const [monthly, setMonthly] = useState(String(store.monthly_amount ?? ""));
  const { busy, error, run } = useAction(close, onDone);

  return (
    <Sheet open={open} onClose={close} title="Ma'lumotlarni tahrirlash">
      <div className="space-y-4">
        <Input label="Nomi" value={name} onChange={(e) => setName(e.target.value)} />
        <Input
          label="Manzil"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
        <NumberInput
          label="Oylik summa (so'm)"
          value={monthly}
          onValueChange={setMonthly}
          hint={monthly ? `${money(Number(monthly))} so'm` : undefined}
        />

        <Card>
          <p className="text-xs text-muted">
            Telefon raqami tahrirlanmaydi — u magazin egasini aniqlash uchun
            ishlatiladi. Raqam noto&apos;g&apos;ri bo&apos;lsa, magazinni
            o&apos;chirib qaytadan yarating.
          </p>
        </Card>

        {error && <Notice tone="error">{error}</Notice>}

        <Button
          disabled={busy || !name.trim() || !address.trim() || monthly === ""}
          onClick={() =>
            run(async () => {
              await adminApi.updateStore(store.id, {
                name: name.trim(),
                address: address.trim(),
                monthly_amount: Number(monthly),
              });
            })
          }
        >
          {busy ? "Saqlanmoqda…" : "Saqlash"}
        </Button>
      </div>
    </Sheet>
  );
}

function InvitePanel({
  store,
  open,
  close,
}: {
  store: Store;
  open: boolean;
  close: () => void;
}) {
  const [link, setLink] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const out = await adminApi.regenerateInvite(store.id);
      setLink(out.link);
      if (!out.link) setError("Botda @username yo'q — havola yaratilmadi.");
      haptic("success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Havola yaratilmadi.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Sheet open={open} onClose={close} title="Taklif havolasi">
      <div className="space-y-4">
        <Card>
          <p className="text-sm text-muted">
            Yangi havola yaratilganda{" "}
            <strong className="text-text">eskisi bekor bo&apos;ladi</strong>.{" "}
            {store.owner_phone ? (
              <>
                Egasi havolani bosib,{" "}
                <code className="nums">{store.owner_phone}</code> raqamli kontaktini
                yuborishi kerak (mos kelmasa ham raqamsiz ulanish tugmasi chiqadi).
              </>
            ) : (
              <>
                Telefon kiritilmagan — egasi havolani bosgan zahoti (hech narsa
                so&apos;ralmasdan) shu magazinga bog&apos;lanadi.
              </>
            )}
          </p>
        </Card>

        {link && (
          <>
            <div className="overflow-x-auto rounded-xl border border-line bg-surface px-3 py-2.5 text-xs">
              <code className="whitespace-nowrap">{link}</code>
            </div>
            <Button
              icon={copied ? <IconCheck size={18} /> : <IconCopy size={18} />}
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(link);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                } catch {
                  setError("Nusxa olinmadi — havolani qo'lda belgilang.");
                }
              }}
            >
              {copied ? "Nusxa olindi" : "Nusxa olish"}
            </Button>
          </>
        )}

        {error && <Notice tone="error">{error}</Notice>}

        <Button tone={link ? "neutral" : "primary"} disabled={busy} onClick={generate}>
          {busy ? "Yaratilmoqda…" : link ? "Yana yangilash" : "Yangi havola yaratish"}
        </Button>
      </div>
    </Sheet>
  );
}

function DeletePanel({
  store,
  open,
  close,
}: {
  store: Store;
  open: boolean;
  close: () => void;
}) {
  const router = useRouter();
  const [confirmText, setConfirmText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Nomni qo'lda yozdirish — tasodifan o'chirib yubormaslik uchun.
  const ok = confirmText.trim() === store.name.trim();

  return (
    <Sheet open={open} onClose={close} title="Magazinni o'chirish">
      <div className="space-y-4">
        <Notice tone="error">
          Magazin bilan birga uning <strong>barcha to&apos;lov tarixi, tok
          yozuvlari va suhbati</strong> o&apos;chadi. Buni qaytarib bo&apos;lmaydi.
        </Notice>

        <Input
          label={`Tasdiqlash uchun magazin nomini yozing: ${store.name}`}
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
          placeholder={store.name}
        />

        {error && <Notice tone="error">{error}</Notice>}

        <Button
          tone="danger"
          disabled={busy || !ok}
          onClick={async () => {
            setBusy(true);
            setError(null);
            try {
              await adminApi.deleteStore(store.id);
              haptic("success");
              router.replace("/app");
            } catch (err) {
              setError(err instanceof ApiError ? err.message : "O'chirilmadi.");
              haptic("error");
              setBusy(false);
            }
          }}
        >
          {busy ? "O'chirilmoqda…" : "Butunlay o'chirish"}
        </Button>
        <Button tone="neutral" disabled={busy} onClick={close}>
          Bekor qilish
        </Button>
      </div>
    </Sheet>
  );
}
