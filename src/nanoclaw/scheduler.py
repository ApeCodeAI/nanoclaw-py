import logging
import time
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from croniter import croniter

from nanoclaw import db
from nanoclaw.agent import run_task_agent
from nanoclaw.config import SCHEDULER_INTERVAL

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def setup_scheduler(bot, db_path: str) -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _check_tasks,
        "interval",
        seconds=SCHEDULER_INTERVAL,
        args=[bot, db_path],
        id="check_tasks",
        replace_existing=True,
    )
    return _scheduler


async def _check_tasks(bot, db_path: str) -> None:
    try:
        tasks = await db.get_due_tasks(db_path)
    except Exception:
        logger.exception("Failed to query due tasks")
        return

    for task in tasks:
        try:
            await _execute_task(task, bot, db_path)
        except Exception:
            logger.exception("Failed to execute task %s", task["id"])


async def _execute_task(task: dict, bot, db_path: str) -> None:
    task_id = task["id"]
    task_chat_id = task["chat_id"]  # Use chat_id from task, not global OWNER_ID
    prompt = task["prompt"]
    logger.info("Executing task %s for chat %s: %s", task_id, task_chat_id, prompt[:80])

    wrapped_prompt = f"You are executing a scheduled task. You MUST use the send_message tool to notify the user in Telegram. Task: {prompt}"
    notify_state = {"sent": False}

    start = time.monotonic()
    try:
        result = await run_task_agent(wrapped_prompt, bot, task_chat_id, db_path, notify_state)

        # Fallback to avoid silent runs when the model forgets to call send_message.
        if not notify_state["sent"]:
            await bot.send_message(chat_id=task_chat_id, text=f"⏰ 定时提醒：{prompt}")

        duration_ms = int((time.monotonic() - start) * 1000)
        await db.log_task_run(db_path, task_id, duration_ms, "success", result=result)
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        await db.log_task_run(db_path, task_id, duration_ms, "error", error=str(e))
        result = f"Error: {e}"

    # Calculate next_run
    stype = task["schedule_type"]
    svalue = task["schedule_value"]
    now = datetime.now(timezone.utc)

    if stype == "cron":
        next_run = croniter(svalue, now).get_next(datetime).isoformat()
        await db.update_task_after_run(db_path, task_id, result, next_run, "active")
    elif stype == "interval":
        next_run = (now + timedelta(milliseconds=int(svalue))).isoformat()
        await db.update_task_after_run(db_path, task_id, result, next_run, "active")
    elif stype == "once":
        await db.update_task_after_run(db_path, task_id, result, None, "completed")
    else:
        logger.warning("Unknown schedule_type %s for task %s", stype, task_id)
