import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from nanoclaw.agent import run_agent, clear_session_id
from nanoclaw.conversations import archive_exchange
from nanoclaw.config import ASSISTANT_NAME, DB_PATH, OWNER_ID, TELEGRAM_BOT_TOKEN
from nanoclaw.scheduler import setup_scheduler

logger = logging.getLogger(__name__)

_TELEGRAM_MAX_LENGTH = 4096


def _is_owner(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id == OWNER_ID


async def _start(update: Update, context) -> None:
    if not _is_owner(update):
        return
    await update.message.reply_text(
        f"Hi! I'm {ASSISTANT_NAME}, your personal AI assistant. Send me a message to get started.\n\n"
        "Commands:\n"
        "/clear - Reset conversation session"
    )


async def _clear(update: Update, context) -> None:
    if not _is_owner(update):
        return
    clear_session_id()
    await update.message.reply_text("Session cleared. Starting fresh!")


async def _handle_message(update: Update, context) -> None:
    if not _is_owner(update) or not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    response = await run_agent(user_text, context.bot, chat_id, str(DB_PATH))

    # Archive to conversations/ for long-term memory
    await archive_exchange(user_text, response, chat_id)

    # Split long messages
    for i in range(0, len(response), _TELEGRAM_MAX_LENGTH):
        chunk = response[i : i + _TELEGRAM_MAX_LENGTH]
        await update.message.reply_text(chunk)


async def _post_init(application: Application) -> None:
    scheduler = setup_scheduler(application.bot, str(DB_PATH))
    scheduler.start()
    logger.info("Scheduler started")


def setup_bot() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CommandHandler("clear", _clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message))
    return app
