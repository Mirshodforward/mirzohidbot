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
