import asyncio
import logging

from nanoclaw.bot import setup_bot
from nanoclaw.config import ASSISTANT_NAME, DATA_DIR, DB_PATH, STORE_DIR, WORKSPACE_DIR
from nanoclaw.db import init_db
from nanoclaw.memory import ensure_workspace

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _async_main() -> None:
    # Create directories
    for d in (WORKSPACE_DIR, STORE_DIR, DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)

    # Initialize database
    await init_db(str(DB_PATH))
    logger.info("Database initialized at %s", DB_PATH)

    # Ensure CLAUDE.md exists
    ensure_workspace()
    logger.info("Workspace ready at %s", WORKSPACE_DIR)

    # Setup and run bot
    app = setup_bot()
    logger.info("%s is starting...", ASSISTANT_NAME)
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Run until interrupted
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
