from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from app.config import get_settings

BTN_CANCEL = "❌ Bekor qilish"
ADMIN_BTN_SKIP_PHONE = "⏭ Telefonsiz davom etish"
USER_BTN_TO_ADMIN = "✉️ Adminga xabar"
USER_BTN_MY_STORE = "🏪 Meni magazinim"

ADMIN_BTN_NEW = "Yangi magazin ➕"
ADMIN_BTN_LIST = "Magazin ro'yxati🗒"
ADMIN_BTN_REPORT = "Magazinlar xisoboti📈"
ADMIN_BTN_MSG = "Xabarlar✉️"
ADMIN_BTN_TOK_PRICE = "💵 Tok narxi (hamma uchun)"

MSG_BROADCAST_ALL = "📢 Barchaga yuborish"
MSG_TO_ONE_STORE = "🏪 Magazinga yuborish"
MSG_MENU_BACK = "⬅️ Asosiy menyuga"

# Menyu tugmalari matni. Erkin matn kutayotgan holatlar (magazin nomi, manzil,
# adminga xabar) bu matnlarni **qiymat sifatida qabul qilmasligi** kerak —
# aks holda tugma bosilganda magazin nomi "Magazin ro'yxati🗒" bo'lib qoladi.
ALL_MENU_TEXTS = frozenset(
    {
        BTN_CANCEL,
        ADMIN_BTN_SKIP_PHONE,
        USER_BTN_TO_ADMIN,
        USER_BTN_MY_STORE,
        ADMIN_BTN_NEW,
        ADMIN_BTN_LIST,
        ADMIN_BTN_REPORT,
        ADMIN_BTN_MSG,
        ADMIN_BTN_TOK_PRICE,
        MSG_BROADCAST_ALL,
        MSG_TO_ONE_STORE,
        MSG_MENU_BACK,
    }
)


def msg_mode_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MSG_BROADCAST_ALL),
                KeyboardButton(text=MSG_TO_ONE_STORE),
            ],
            [KeyboardButton(text=MSG_MENU_BACK)],
        ],
        resize_keyboard=True,
    )


def contact_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktni ulashish", request_contact=True)],
        ],
        resize_keyboard=True,
    )


def admin_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADMIN_BTN_NEW),
                KeyboardButton(text=ADMIN_BTN_LIST),
            ],
            [
                KeyboardButton(text=ADMIN_BTN_REPORT),
                KeyboardButton(text=ADMIN_BTN_MSG),
            ],
            [KeyboardButton(text=ADMIN_BTN_TOK_PRICE)],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def phone_step_keyboard() -> ReplyKeyboardMarkup:
    """Magazin yaratishda telefon so'ralayotgan qadam — ixtiyoriy, o'tkazib yuborish mumkin."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_BTN_SKIP_PHONE)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def user_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=USER_BTN_MY_STORE),
                KeyboardButton(text=USER_BTN_TO_ADMIN),
            ],
        ],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# --- Mini App ---------------------------------------------------------------


def miniapp_url(path: str = "/app") -> str | None:
    """Mini App manzili. HTTPS bo'lmasa None — Telegram http'ni rad etadi.

    Lokal ishlab chiqishda (PUBLIC_BASE_URL=http://localhost:8000) tugma
    umuman ko'rsatilmaydi, aks holda bot "Bad Request: bad webapp url" beradi.
    """
    base = (get_settings().public_base_url or "").strip().rstrip("/")
    if not base.startswith("https://"):
        return None
    return base + path


def miniapp_inline_keyboard(*, is_admin: bool) -> InlineKeyboardMarkup | None:
    """/start dagi Mini App tugmasi. Admin boshqaruvga, egasi kabinetga tushadi."""
    if is_admin:
        url = miniapp_url("/app/admin")
        text = "📊 Admin panelni ochish"
    else:
        url = miniapp_url("/app")
        text = "🏪 Mening kabinetim"
    if not url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))]]
    )


def store_date_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Bugungi sana",
                    callback_data="store:date:auto",
                ),
                InlineKeyboardButton(
                    text="✏️ Qo'lda kiritish",
                    callback_data="store:date:manual",
                ),
            ],
        ],
    )
