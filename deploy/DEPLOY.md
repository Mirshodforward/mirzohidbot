# Deploy — 161.35.27.123 (Ubuntu 22.04, nginx 1.18)

## Nega Docker/Caddy emas

Bu serverda:

* **nginx allaqachon 80/443 ni egallagan** va `api.axisstars.uz` bilan birga
  boshqa loyihalarga (kinobot, paymee, premiumtg, xprem) xizmat qilmoqda.
  `docker-compose.yml` dagi Caddy konteyneri port band bo'lgani uchun
  ko'tarilmaydi — ko'tarilsa esa o'sha saytlarni buzadi.
* **PostgreSQL native o'rnatilgan va `mirzohid_db` ichida real ma'lumot bor.**
  Bazani konteynerga ko'chirish keraksiz xavf.
* Disk 24 GB dan 72% band (~6.7 GB bo'sh), xotira 70%, swap 36%.
  Docker daemon + image'lar bu yerda qimmatga tushadi.

Shuning uchun: **systemd + mavjud nginx + mavjud Postgres**. Bu sizning
boshqa loyihalaringiz bilan bir xil uslub.

Portlar: API `127.0.0.1:8801`, Web `127.0.0.1:3801` — faqat localhost'da,
tashqariga nginx chiqaradi. **Deploy oldidan band emasligini tekshiring:**

```bash
sudo ss -tlnp | grep -E ':(8801|3801)\b' || echo "ikkala port ham bo'sh"
```

---

## 0. Tayyorgarlik: bazani tekshirish va zaxira

```bash
sudo -u postgres psql -c "\l" | grep mirzohid
sudo -u postgres psql -d mirzohid_db -c "\dt"
sudo -u postgres psql -d mirzohid_db -c \
  "SELECT (SELECT count(*) FROM stores) AS magazinlar,
          (SELECT count(*) FROM users)  AS foydalanuvchilar;"

# ZAXIRA — migratsiyadan oldin majburiy
sudo -u postgres pg_dump mirzohid_db > /root/mirzohid_db_$(date +%F_%H%M).sql
ls -lh /root/mirzohid_db_*.sql
```

## 1. Foydalanuvchi va kod

```bash
sudo adduser --system --group --home /opt/mirzohid mirzohid
sudo git clone https://github.com/Mirshodforward/mirzohidbot.git /opt/mirzohid
cd /opt/mirzohid
sudo git checkout feat/monorepo-miniapp
sudo mkdir -p backups
sudo chown -R mirzohid:mirzohid /opt/mirzohid
```

## 2. .env

```bash
sudo -u mirzohid cp .env.example .env
sudo -u mirzohid nano .env
sudo chmod 600 /opt/mirzohid/.env
```

To'ldirish kerak:

```ini
DATABASE_URL=postgresql+asyncpg://miniuser:YANGI_PAROL@localhost:5432/mirzohid_db
BOT_TOKEN=<bot tokeni>
ADMIN_IDS=<telegram id lar, vergul bilan>

PUBLIC_BASE_URL=https://SUBDOMAIN.DOMEN.uz
CORS_ORIGINS=https://SUBDOMAIN.DOMEN.uz
USE_WEBHOOK=true

JWT_SECRET=<pastdagi buyruq bilan>
WEBHOOK_SECRET=<pastdagi buyruq bilan>

REMINDER_HOUR=9
REMINDER_MINUTE=0
```

Sirlarni generatsiya qilish:

```bash
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(48))"
python3 -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
```

**Postgres parolini almashtirish** (eskisi ochiq kanalda yozilgan):

```bash
sudo -u postgres psql -c "ALTER USER miniuser WITH PASSWORD 'YANGI_PAROL';"
# keyin .env dagi DATABASE_URL ni yangilang
```

## 3. Backend

```bash
cd /opt/mirzohid/apps/api
sudo -u mirzohid python3 -m venv .venv
sudo -u mirzohid .venv/bin/pip install -r requirements.txt

# Jadvallar allaqachon bor — 0001 ni QAYTA YARATMAYMIZ, faqat belgilaymiz
sudo -u mirzohid .venv/bin/alembic stamp 0001
sudo -u mirzohid .venv/bin/alembic upgrade head    # faqat login_codes qo'shiladi
sudo -u mirzohid .venv/bin/alembic current
```

## 4. Frontend

```bash
node -v    # 20+ kerak; yo'q bo'lsa:
# curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs

cd /opt/mirzohid/apps/web
sudo -u mirzohid npm ci
sudo -u mirzohid npm run build

# standalone build o'z ichiga static/public ni olmaydi — ko'chiramiz
sudo -u mirzohid cp -r public .next/standalone/ 2>/dev/null || true
sudo -u mirzohid cp -r .next/static .next/standalone/.next/
```

## 5. systemd

```bash
sudo cp /opt/mirzohid/deploy/mirzohid-api.service /etc/systemd/system/
sudo cp /opt/mirzohid/deploy/mirzohid-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mirzohid-api mirzohid-web

sudo systemctl status mirzohid-api --no-pager
curl -s http://127.0.0.1:8801/health     # {"status":"ok"}
curl -sI http://127.0.0.1:3801/ | head -1
```

## 6. nginx + HTTPS

```bash
sudo cp /opt/mirzohid/deploy/nginx-mirzohid.conf /etc/nginx/sites-available/mirzohid
sudo sed -i 's/SUBDOMAIN.DOMEN.uz/haqiqiy.domeningiz.uz/' /etc/nginx/sites-available/mirzohid
sudo ln -s /etc/nginx/sites-available/mirzohid /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# DNS tarqalgach:
sudo certbot --nginx -d haqiqiy.domeningiz.uz
```

## 7. Telegram

Webhook `USE_WEBHOOK=true` bo'lsa API ko'tarilganda avtomatik o'rnatiladi.
Tekshirish:

```bash
source /opt/mirzohid/.env
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo" | python3 -m json.tool
```

`"url"` sizning domeningiz bo'lishi va `"last_error_message"` bo'sh bo'lishi kerak.

Mini App'ni ulash: @BotFather → bot → **Bot Settings → Menu Button →
Configure menu button** → `https://haqiqiy.domeningiz.uz/app`

## 8. Eski botni o'chirish

**Muhim:** eski `python main.py` jarayoni hali ishlayotgan bo'lsa, u polling
qiladi va yangi webhook bilan konflikt beradi.

```bash
ps aux | grep -E "main\.py|mirzohid" | grep -v grep
sudo systemctl list-units --type=service | grep -i mirzohid
# topilganini to'xtating va disable qiling
```

---

## Loglar

```bash
sudo journalctl -u mirzohid-api -f
sudo journalctl -u mirzohid-web -f
sudo tail -f /var/log/nginx/mirzohid.error.log
```

## Yangilash

```bash
cd /opt/mirzohid && sudo -u mirzohid git pull
cd apps/api && sudo -u mirzohid .venv/bin/pip install -r requirements.txt \
  && sudo -u mirzohid .venv/bin/alembic upgrade head
cd ../web && sudo -u mirzohid npm ci && sudo -u mirzohid npm run build \
  && sudo -u mirzohid cp -r .next/static .next/standalone/.next/
sudo systemctl restart mirzohid-api mirzohid-web
```

## Orqaga qaytarish

```bash
sudo systemctl stop mirzohid-api mirzohid-web
sudo -u postgres psql -d mirzohid_db < /root/mirzohid_db_<sana>.sql
# eski botni qayta yoqing
```

---

## Haqiqiy deploy (2026-08-07) — nima boshqacha bo'ldi

Yuqoridagi umumiy qadamlardan farqlari. Ular serverni ko'rgandan keyin
majburan o'zgardi:

### 1. Alohida DB foydalanuvchisi — `miniuser` EMAS

`miniuser` **9 ta bazaga** egalik qiladi va **5 ta ishlab turgan loyiha**
(kinobot, oxangxbot, paymee, premiumtg, xprem) o'sha parol bilan ulanadi.
Uning parolini almashtirish ularni bir zumda o'chiradi.

Shuning uchun Mirzohid uchun alohida rol ochildi:

```sql
CREATE ROLE mirzohid_app LOGIN PASSWORD '<tasodifiy 32 belgi>';
GRANT CONNECT ON DATABASE mirzohid_db TO mirzohid_app;
-- mirzohid_db ichida:
GRANT USAGE, CREATE ON SCHEMA public TO mirzohid_app;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO mirzohid_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mirzohid_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO mirzohid_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mirzohid_app;
```

Bu rol faqat `mirzohid_db` ni ko'radi — boshqa 8 ta bazaga kira olmaydi.

### 2. Frontend LOKAL build qilinadi, serverda emas

Serverda 957 MB xotira va ~180 MB bo'sh joy bor, `swapfile` esa 100% to'la.
`npm run build` (~0.5–1 GB) shu yerda OOM killer'ni uyg'otib, ishlab turgan
loyihalarni o'ldirishi mumkin.

Shuning uchun build ishlab chiquvchi mashinasida qilinadi va **artefakt**
jo'natiladi:

```bash
# lokal mashinada
cd apps/web
API_ORIGIN=http://127.0.0.1:8801 npm run build     # <-- API_ORIGIN MAJBURIY
cp -r .next/static .next/standalone/.next/
cp -r public .next/standalone/
tar czf /tmp/mrz_web.tgz -C .next standalone
scp /tmp/mrz_web.tgz root@SERVER:/tmp/

# serverda
systemctl stop mirzohid-web
rm -rf /opt/mirzohid/apps/web/.next/standalone
tar xzf /tmp/mrz_web.tgz -C /opt/mirzohid/apps/web/.next/
chown -R mirzohid:mirzohid /opt/mirzohid/apps/web
systemctl start mirzohid-web
```

**`API_ORIGIN` ni build paytida berish shart.** Next `rewrites()` manzilini
`routes-manifest.json` ga yozib qo'yadi; standalone rejimda ishga tushganda
muhit o'zgaruvchisi qayta o'qilmaydi. Bersangiz — `/api/*` ishlaydi,
bermasangiz `localhost:8000` qotib qoladi va 500 qaytaradi.

`next.config.ts` da `images.unoptimized = true` — aks holda standalone
build'ga build qilingan platformaning `sharp` binarisi tushadi (Windows'da
build qilinsa `sharp-win32-x64`) va u Linuxda ishlamaydi.

### 3. Python 3.10

Server Ubuntu 22.04 / Python 3.10. Kod shunga moslashtirilgan
(`StrEnum` va `datetime.UTC` ishlatilmaydi). `python3.10-venv` allaqachon
o'rnatilgan edi.

### 4. Xotira

Deploy dan keyin: uvicorn ~174 MB, next-server ~68 MB, bo'sh ~179 MB,
`swapfile` (2 GB) 100% to'la. OOM bo'lmadi, lekin zaxira deyarli yo'q.
Droplet'ni 2 GB ga ko'tarish tavsiya qilinadi.
