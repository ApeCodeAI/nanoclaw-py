"""Conversation archiving for long-term memory."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from nanoclaw.config import WORKSPACE_DIR

logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = WORKSPACE_DIR / "conversations"


def ensure_conversations_dir() -> None:
    """Create conversations directory if it doesn't exist."""
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _get_today_file() -> Path:
    """Get the conversation file for today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return CONVERSATIONS_DIR / f"{today}.md"


async def archive_exchange(user_message: str, assistant_response: str, chat_id: int) -> None:
    """Archive a single user-assistant exchange to today's conversation file.

    Format:
    ## HH:MM:SS UTC

    **User**: <message>

    **Ape**: <response>

    ---
    """
    ensure_conversations_dir()

    filepath = _get_today_file()
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    # Build the exchange entry
    entry = f"""## {timestamp}

**User**: {user_message}

**Ape**: {assistant_response}

---

"""

    # Append to file (create if doesn't exist)
    try:
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
        else:
            # Create file with header
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            content = f"# Conversations - {date_str}\n\n"

        content += entry
        filepath.write_text(content, encoding="utf-8")
        logger.debug(f"Archived exchange to {filepath}")
    except Exception:
        logger.exception(f"Failed to archive exchange to {filepath}")
