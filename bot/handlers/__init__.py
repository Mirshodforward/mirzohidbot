from aiogram import Dispatcher

from bot.handlers.admin import router as admin_router
from bot.handlers.admin_stores import router as admin_stores_router
from bot.handlers.start import router as start_router
from bot.handlers.user import router as user_router


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(admin_stores_router)
    dp.include_router(user_router)
