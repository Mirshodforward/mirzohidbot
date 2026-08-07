"""APScheduler — fon vazifalari uchun yagona vaqt manbai.

Nega uchta vazifa:

* ``accrual``            — soatiga bir marta 30 kunlik sikllarni qarzga qo'shadi.
* ``reminders``          — aniq soat 09:00 (Toshkent) da eslatma yuboradi.
* ``reminders_catchup``  — soatiga bir marta: agar 09:00 da server o'chiq bo'lgan
  bo'lsa, ko'tarilgach o'sha kunning eslatmasi baribir ketadi. Vazifa idempotent
  (``rent_reminder_sent_for``), shuning uchun ikki marta yuborilmaydi.

Scheduler faqat advisory lock'ni ushlagan jarayonda ishga tushadi — bir nechta
uvicorn worker bo'lsa ham qarz bir marta hisoblanadi.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.domain.store_flow import TZ_TASHKENT

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _job_accrual() -> None:
    from app.services.reminders import run_rent_accrual_pass

    await run_rent_accrual_pass()


async def _job_reminders() -> None:
    from app.bot.dispatcher import get_bot
    from app.services.reminders import send_due_reminders

    await send_due_reminders(get_bot())


async def _job_reminders_catchup() -> None:
    from app.bot.dispatcher import get_bot
    from app.services.reminders import send_due_reminders

    await send_due_reminders(get_bot(), enforce_hour=True)


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    s = get_settings()
    sched = AsyncIOScheduler(timezone=TZ_TASHKENT)

    sched.add_job(
        _job_accrual,
        IntervalTrigger(hours=1),
        id="accrual",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    sched.add_job(
        _job_reminders,
        CronTrigger(hour=s.reminder_hour, minute=s.reminder_minute, timezone=TZ_TASHKENT),
        id="reminders",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        replace_existing=True,
    )
    sched.add_job(
        _job_reminders_catchup,
        IntervalTrigger(hours=1),
        id="reminders_catchup",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    sched.start()
    _scheduler = sched
    logger.info(
        "Scheduler ishga tushdi: eslatma har kuni %02d:%02d (Asia/Tashkent).",
        s.reminder_hour,
        s.reminder_minute,
    )
    return sched


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler to'xtatildi.")
