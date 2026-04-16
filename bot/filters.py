from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from bot.config import is_admin


class AdminFilter(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        u = event.from_user
        return bool(u and is_admin(u.id))
