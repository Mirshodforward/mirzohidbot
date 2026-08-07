# Mirzohid — magazin ijarasi boshqaruvi

Telegram bot, Telegram Mini App va sayt — **bitta kod bazasi, bitta baza, bitta jarayon**.

```
mirzohid/
├─ apps/
│  ├─ api/                 FastAPI + aiogram (webhook) + APScheduler
│  │  ├─ app/
│  │  │  ├─ api/v1/        REST endpointlar (auth, stores, admin)
│  │  │  ├─ bot/           aiogram: handlers, keyboards, webhook
│  │  │  ├─ core/          JWT, Telegram initData, dependency'lar
│  │  │  ├─ db/            SQLAlchemy modellari va sessiya
│  │  │  ├─ domain/        sof biznes qoidalari (qarz sikllari, sana, telefon)
│  │  │  ├─ schemas/       Pydantic DTO
│  │  │  └─ services/      bot va API uchun **umumiy** amallar
│  │  └─ alembic/          migratsiyalar
│  └─ web/                 Next.js 15 — sayt + Mini App
│     ├─ app/              (/) sayt · (/kirish) login · (/app) kabinet+MiniApp
│     ├─ components/
│     └─ lib/              API klient, Telegram wrapper, formatlash
├─ scripts/                backup.py · send.py · tikla.py · reset.py
├─ docker-compose.yml
└─ Caddyfile
```

## Nima qayerda ishlaydi

| Kirish nuqtasi | Manzil | Auth |
|---|---|---|
| Sayt | `https://<domen>/` | telefon → bot kodi → JWT (httpOnly cookie) |
| Mini App | `https://<domen>/app` | Telegram `initData` HMAC → JWT (sessionStorage) |
| Bot | Telegram | `ADMIN_IDS` + telefon orqali bog'lanish |
| Webhook | `POST /telegram/webhook/<WEBHOOK_SECRET>` | secret yo'l + secret sarlavha |

Bot va API **bitta jarayonda** yashaydi. Aynan shu narsa avvalgi
`TelegramConflictError` ni yo'q qiladi: update manbai bitta.

---

## Ishga tushirish (lokal)

```bash
cp .env.example .env      # DATABASE_URL, BOT_TOKEN, ADMIN_IDS ni to'ldiring
                          # USE_WEBHOOK=false qoldiring — bot polling bilan ishlaydi

# --- Backend ---
cd apps/api
python -m venv .venv && .venv/Scripts/activate     # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# --- Frontend (yangi terminal) ---
cd apps/web
npm install
npm run dev                                        # http://localhost:3000
```

API hujjatlari: <http://localhost:8000/docs>

## Mavjud bazaga ko'chirish

Jadvallar allaqachon bor, shuning uchun `0001` ni **qayta yaratmaymiz**, faqat belgilaymiz:

```bash
cd apps/api
alembic stamp 0001      # "bu sxema allaqachon qo'llangan"
alembic upgrade head    # faqat 0002 (login_codes) qo'shiladi
```

Avval zaxira oling: `python scripts/backup.py`

## Production (Docker Compose + Caddy)

```bash
cp .env.example .env
# DOMAIN, POSTGRES_PASSWORD, BOT_TOKEN, ADMIN_IDS,
# JWT_SECRET, WEBHOOK_SECRET ni to'ldiring, USE_WEBHOOK=true qiling

docker compose up -d --build
docker compose logs -f api
```

Sirlarni generatsiya qilish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Caddy HTTPS sertifikatini o'zi oladi. Webhook `api` ko'tarilganda avtomatik
o'rnatiladi (`USE_WEBHOOK=true` bo'lsa).

### Mini App'ni Telegramga ulash

@BotFather → botingiz → **Bot Settings → Menu Button → Configure menu button**
→ URL: `https://<domen>/app`

---

## Fon vazifalari

| Vazifa | Vaqti | Nima qiladi |
|---|---|---|
| `accrual` | soatiga 1 marta | 30 kunlik davr kelganda oylikni qarzga qo'shadi |
| `reminders` | har kuni `REMINDER_HOUR:REMINDER_MINUTE` (Asia/Tashkent) | qarzdorlarga eslatma |
| `reminders_catchup` | soatiga 1 marta | server 09:00 da o'chiq bo'lgan bo'lsa, kunni o'tkazib yubormaydi |

Uchalasi ham **idempotent** — kuniga bir marta yuboriladi
(`stores.rent_reminder_sent_for`), necha marta chaqirilishidan qat'i nazar.

Bir nechta uvicorn worker ishlatilsa, bot va scheduler faqat Postgres advisory
lock'ni olgan jarayonda ishga tushadi — qarz ikki marta hisoblanmaydi.

## Skriptlar

```bash
python scripts/backup.py               # DB zaxirasi -> backups/
python scripts/send.py --make-backup   # zaxira olib, Telegramga yuborish
python scripts/tikla.py --yes          # zaxiradan tiklash
```

`backups/` va `*.sql` `.gitignore` da — ichida real telefon raqamlari bor.

## Sifat tekshiruvi

```bash
cd apps/api && ruff check app/
cd apps/web && npm run typecheck && npm run build
```

TypeScript tiplarini OpenAPI'dan generatsiya qilish (API ishlab turganda):

```bash
cd apps/web && npm run gen:api
```
