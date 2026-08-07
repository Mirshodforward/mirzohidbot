"""FastAPI ilovasi: REST API + Telegram bot + scheduler — bitta jarayonda."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.bot.webhook import register_webhook_route, setup_webhook, teardown_webhook
from app.config import get_settings
from app.db.session import acquire_single_instance_lock, release_single_instance_lock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Fon vazifalariga havola — `create_task` natijasi saqlanmasa, CPython uni
# istalgan paytda yig'ib yuborishi mumkin va bot jimgina to'xtaydi.
_background: set[asyncio.Task] = set()


def _spawn(coro, name: str) -> None:
    task = asyncio.create_task(coro, name=name)
    _background.add(task)
    task.add_done_callback(_background.discard)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.bot.dispatcher import close_bot, get_bot, get_dispatcher
    from app.services.scheduler import shutdown_scheduler, start_scheduler

    # Faqat bitta jarayon botni va schedulerni yuritadi. Qolgan workerlar
    # oddiy API server bo'lib qolaveradi.
    is_leader = await acquire_single_instance_lock()
    if not is_leader:
        logger.info("Bu jarayon leader emas: bot va scheduler ishga tushirilmaydi.")

    if is_leader and settings.bot_token.strip():
        if settings.use_webhook:
            await setup_webhook()
        else:
            # Lokal ishlab chiqish: HTTPS domen shart emas.
            logger.info("USE_WEBHOOK=false — bot polling rejimida ishlaydi.")
            bot, dp = get_bot(), get_dispatcher()
            await bot.delete_webhook(drop_pending_updates=False)
            _spawn(dp.start_polling(bot, handle_signals=False), "polling")
        start_scheduler()
    elif not settings.bot_token.strip():
        logger.warning("BOT_TOKEN bo'sh — bot funksiyalari o'chirilgan.")

    try:
        yield
    finally:
        for task in list(_background):
            task.cancel()
        for task in list(_background):
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: B014
                pass
        if is_leader:
            shutdown_scheduler()
            if settings.use_webhook:
                await teardown_webhook()
            await release_single_instance_lock()
        await close_bot()


app = FastAPI(
    title="Mirzohid API",
    description="Magazin ijarasi: Telegram bot, Mini App va sayt uchun umumiy API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,  # httpOnly cookie sayt uchun
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
register_webhook_route(app)


@app.get("/health", tags=["service"])
async def health() -> dict:
    return {"status": "ok"}
