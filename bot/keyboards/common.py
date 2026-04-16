from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BTN_CANCEL = "❌ Bekor qilish"
USER_BTN_TO_ADMIN = "✉️ Adminga xabar"
USER_BTN_MY_STORE = "🏪 Meni magazinim"

ADMIN_BTN_NEW = "Yangi magazin ➕"
ADMIN_BTN_LIST = "Magazin ro'yxati🗒"
ADMIN_BTN_REPORT = "Magazinlar xisoboti📈"
ADMIN_BTN_MSG = "Xabarlar✉️"


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
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
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


def store_date_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Avto (Toshkent)",
                    callback_data="store:date:auto",
                ),
                InlineKeyboardButton(
                    text="✏️ Qo'lda",
                    callback_data="store:date:manual",
                ),
            ],
        ],
    )
