/**
 * API klient.
 *
 * So'rovlar `/api/...` ga ketadi va Next rewrite orqali FastAPI ga uzatiladi
 * (next.config.ts). Shu tufayli brauzer uchun frontend va backend bitta origin:
 * httpOnly cookie muammosiz ishlaydi va CORS umuman kerak emas.
 *
 * Mini App'da esa cookie ishonchsiz (iframe + uchinchi tomon cookie cheklovi),
 * shuning uchun token `sessionStorage` da saqlanadi va `Authorization`
 * sarlavhasida yuboriladi. Ikkala yo'l ham bir xil JWT bilan ishlaydi.
 */

const TOKEN_KEY = "mrz_token";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function setToken(token: string): void {
  if (typeof window !== "undefined") sessionStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  if (typeof window !== "undefined") sessionStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`/api/v1${path}`, {
    ...init,
    headers,
    credentials: "include", // sayt uchun httpOnly cookie
  });

  if (res.status === 204) return undefined as T;

  const raw = await res.text();
  const data = raw ? JSON.parse(raw) : null;

  if (!res.ok) {
    // FastAPI xatoni `detail` da qaytaradi; validatsiya xatosi massiv bo'lishi mumkin.
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg ?? "").join(", ")
          : `So'rov bajarilmadi (${res.status})`;
    throw new ApiError(message, res.status);
  }
  return data as T;
}

// --- Tiplar (backend schemas/ bilan mos; `npm run gen:api` bilan generatsiya ham mumkin) ---

export interface Store {
  id: number;
  name: string;
  description: string | null;
  address: string | null;
  owner_phone: string | null;
  owner_telegram_id: number | null;
  store_date: string | null;
  monthly_amount: number | null;
  electricity_kw: number | null;
  debt_tok: number;
  debt_balance: number;
  created_at: string | null;
  next_payment_at: string | null;
  electricity_price_per_kw: number | null;
  electricity_due: number | null;
}

export interface Me {
  id: number;
  telegram_id: number | null;
  phone_number: string | null;
  full_name: string | null;
  username: string | null;
  is_admin: boolean;
  store_count: number;
}

export interface Payment {
  id: number;
  store_id: number;
  amount: number;
  debt_after: number;
  created_at: string;
  created_by_telegram_id: number;
}

export interface ElectricityLog {
  id: number;
  store_id: number;
  period_from: string;
  period_to: string;
  reading_before: number;
  reading_after: number;
  delta_kw: number;
  created_at: string;
}

export interface ChatMessage {
  id: number;
  store_id: number;
  from_admin: boolean;
  body: string;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_sec: number;
}

export interface Stats {
  stores: number;
  users: number;
  linked_users: number;
  total_debt: number;
  generated_at: string;
}

export interface Invite {
  token: string;
  link: string | null;
}

export interface StoreCreated {
  store: Store;
  invite_link: string | null;
  invite_token: string | null;
}

export interface StoreCreateInput {
  name: string;
  owner_phone?: string;
  address: string;
  monthly_amount: number;
  electricity_kw: number;
  store_date?: string | null;
  description?: string | null;
}

export interface StoreUpdateInput {
  name?: string;
  address?: string;
  monthly_amount?: number;
  description?: string | null;
}

export const api = {
  loginTelegram: async (initData: string): Promise<TokenResponse> => {
    const out = await request<TokenResponse>("/auth/telegram", {
      method: "POST",
      body: JSON.stringify({ init_data: initData }),
    });
    setToken(out.access_token);
    return out;
  },

  requestCode: (phone: string) =>
    request<{ sent: boolean; expires_in_sec: number; message: string }>(
      "/auth/request-code",
      { method: "POST", body: JSON.stringify({ phone }) },
    ),

  verifyCode: async (phone: string, code: string): Promise<TokenResponse> => {
    const out = await request<TokenResponse>("/auth/verify-code", {
      method: "POST",
      body: JSON.stringify({ phone, code }),
    });
    setToken(out.access_token);
    return out;
  },

  logout: async () => {
    await request<void>("/auth/logout", { method: "POST" });
    clearToken();
  },

  me: () => request<Me>("/auth/me"),
  stores: () => request<Store[]>("/stores"),
  store: (id: number) => request<Store>(`/stores/${id}`),
  payments: (id: number) => request<Payment[]>(`/stores/${id}/payments`),
  electricity: (id: number) => request<ElectricityLog[]>(`/stores/${id}/electricity`),
  messages: (id: number) => request<ChatMessage[]>(`/stores/${id}/messages`),
  sendMessage: (id: number, body: string) =>
    request<ChatMessage>(`/stores/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({ body }),
    }),
};

/** Faqat admin uchun. Token adminniki bo'lmasa server 403 qaytaradi. */
export const adminApi = {
  stats: () => request<Stats>("/admin/stats"),

  createStore: (data: StoreCreateInput) =>
    request<StoreCreated>("/admin/stores", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateStore: (id: number, data: StoreUpdateInput) =>
    request<Store>(`/admin/stores/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteStore: (id: number) =>
    request<void>(`/admin/stores/${id}`, { method: "DELETE" }),

  addPayment: (id: number, amount: number) =>
    request<Payment>(`/admin/stores/${id}/payments`, {
      method: "POST",
      body: JSON.stringify({ amount }),
    }),

  addReading: (id: number, reading: number) =>
    request<Store>(`/admin/stores/${id}/electricity`, {
      method: "POST",
      body: JSON.stringify({ reading }),
    }),

  regenerateInvite: (id: number) =>
    request<Invite>(`/admin/stores/${id}/invite`, { method: "POST" }),

  getPrice: () =>
    request<{ price_per_kw: number | null }>("/admin/settings/electricity-price"),

  setPrice: (price_per_kw: number) =>
    request<{ price_per_kw: number | null }>("/admin/settings/electricity-price", {
      method: "PUT",
      body: JSON.stringify({ price_per_kw }),
    }),

  broadcast: (text: string) =>
    request<{ sent: number; blocked: number; failed: number }>("/admin/broadcast", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  /** Excel yuklab olish — blob sifatida, keyin brauzerda saqlanadi. */
  downloadExcel: async (kind: "stores" | "full-report"): Promise<void> => {
    const headers = new Headers();
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    const res = await fetch(`/api/v1/admin/export/${kind}.xlsx`, {
      headers,
      credentials: "include",
    });
    if (!res.ok) throw new ApiError("Fayl yuklanmadi", res.status);

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = kind === "stores" ? "magazinlar.xlsx" : "mirzohid_hisobot.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    // Brauzer yuklab bo'lgunicha biroz kutamiz, keyin xotirani bo'shatamiz.
    setTimeout(() => URL.revokeObjectURL(url), 10_000);
  },
};
