import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    query,
    tool,
)
from croniter import croniter

from nanoclaw import db
from nanoclaw.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_BASE_URL,
    DATA_DIR,
    STATE_FILE,
    WORKSPACE_DIR,
)

logger = logging.getLogger(__name__)
_agent_lock = asyncio.Lock()


def _create_tools(bot: Any, chat_id: int, db_path: str) -> list:
    @tool("send_message", "Send a message to the user on Telegram", {"text": str})
    async def send_message(args: dict[str, Any]) -> dict[str, Any]:
        await bot.send_message(chat_id=chat_id, text=args["text"])
        return {"content": [{"type": "text", "text": "Message sent."}]}

    @tool(
        "schedule_task",
        "Schedule a task. schedule_type: 'cron', 'interval', or 'once'. "
        "schedule_value: cron expression, milliseconds, or ISO timestamp.",
        {"prompt": str, "schedule_type": str, "schedule_value": str},
    )
    async def schedule_task(args: dict[str, Any]) -> dict[str, Any]:
        stype = args["schedule_type"]
        svalue = args["schedule_value"]
        now = datetime.now(timezone.utc)

        if stype == "cron":
            next_run = croniter(svalue, now).get_next(datetime).isoformat()
        elif stype == "interval":
            next_run = (now + timedelta(milliseconds=int(svalue))).isoformat()
        elif stype == "once":
            next_run = svalue
        else:
            return {"content": [{"type": "text", "text": f"Unknown schedule_type: {stype}"}], "is_error": True}

        task_id = await db.create_task(db_path, chat_id, args["prompt"], stype, svalue, next_run)
        return {"content": [{"type": "text", "text": f"Task {task_id} scheduled. Next run: {next_run}"}]}

    @tool("list_tasks", "List all scheduled tasks", {})
    async def list_tasks(args: dict[str, Any]) -> dict[str, Any]:
        tasks = await db.get_all_tasks(db_path)
        if not tasks:
            return {"content": [{"type": "text", "text": "No scheduled tasks."}]}
        lines = [f"- [{t['id']}] {t['status']} | {t['schedule_type']}({t['schedule_value']}) | {t['prompt'][:60]}" for t in tasks]
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    @tool("pause_task", "Pause a scheduled task", {"task_id": str})
    async def pause_task(args: dict[str, Any]) -> dict[str, Any]:
        ok = await db.update_task_status(db_path, args["task_id"], "paused")
        msg = f"Task {args['task_id']} paused." if ok else f"Task {args['task_id']} not found."
        return {"content": [{"type": "text", "text": msg}]}

    @tool("resume_task", "Resume a paused task", {"task_id": str})
    async def resume_task(args: dict[str, Any]) -> dict[str, Any]:
        ok = await db.update_task_status(db_path, args["task_id"], "active")
        msg = f"Task {args['task_id']} resumed." if ok else f"Task {args['task_id']} not found."
        return {"content": [{"type": "text", "text": msg}]}

    @tool("cancel_task", "Cancel and delete a scheduled task", {"task_id": str})
    async def cancel_task(args: dict[str, Any]) -> dict[str, Any]:
        ok = await db.delete_task(db_path, args["task_id"])
        msg = f"Task {args['task_id']} cancelled." if ok else f"Task {args['task_id']} not found."
        return {"content": [{"type": "text", "text": msg}]}

    return [send_message, schedule_task, list_tasks, pause_task, resume_task, cancel_task]


def _load_session_id() -> str | None:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
        return data.get("session_id")
    return None


def _save_session_id(session_id: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"session_id": session_id}))


def clear_session_id() -> None:
    if STATE_FILE.exists():
        STATE_FILE.unlink()


async def _make_prompt(text: str) -> AsyncGenerator[dict, None]:
    """Create async generator prompt to work around SDK MCP bug."""
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": text
        }
    }


async def run_agent(prompt: str, bot: Any, chat_id: int, db_path: str) -> str:
    async with _agent_lock:
        return await _run_agent_inner(prompt, bot, chat_id, db_path)


async def _run_agent_inner(prompt: str, bot: Any, chat_id: int, db_path: str) -> str:
    tools = _create_tools(bot, chat_id, db_path)
    mcp_server = create_sdk_mcp_server(name="nanoclaw", tools=tools)

    session_id = _load_session_id()

    env = {"ANTHROPIC_API_KEY": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        env["ANTHROPIC_BASE_URL"] = ANTHROPIC_BASE_URL

    options = ClaudeAgentOptions(
        cwd=str(WORKSPACE_DIR),
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "WebSearch", "WebFetch",
            "mcp__nanoclaw__send_message",
            "mcp__nanoclaw__schedule_task",
            "mcp__nanoclaw__list_tasks",
            "mcp__nanoclaw__pause_task",
            "mcp__nanoclaw__resume_task",
            "mcp__nanoclaw__cancel_task",
        ],
        permission_mode="bypassPermissions",
        mcp_servers={"nanoclaw": mcp_server},
        env=env,
    )
    if session_id:
        options.resume = session_id

    response_parts: list[str] = []

    try:
        async for message in query(prompt=_make_prompt(prompt), options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            elif isinstance(message, ResultMessage):
                _save_session_id(message.session_id)
                if message.result:
                    response_parts.append(message.result)
    except Exception:
        if not response_parts:
            logger.exception("Agent error")
            return "Sorry, something went wrong while processing your request."
        logger.debug("Ignoring query cleanup error", exc_info=True)

    return "".join(response_parts) or "Done."


async def run_task_agent(prompt: str, bot: Any, chat_id: int, db_path: str) -> str:
    """Run agent for scheduled tasks — no session resume."""
    tools = _create_tools(bot, chat_id, db_path)
    mcp_server = create_sdk_mcp_server(name="nanoclaw", tools=tools)

    env = {"ANTHROPIC_API_KEY": ANTHROPIC_API_KEY}
    if ANTHROPIC_BASE_URL:
        env["ANTHROPIC_BASE_URL"] = ANTHROPIC_BASE_URL

    options = ClaudeAgentOptions(
        cwd=str(WORKSPACE_DIR),
        allowed_tools=[
            "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "WebSearch", "WebFetch",
            "mcp__nanoclaw__send_message",
            "mcp__nanoclaw__schedule_task",
            "mcp__nanoclaw__list_tasks",
            "mcp__nanoclaw__pause_task",
            "mcp__nanoclaw__resume_task",
            "mcp__nanoclaw__cancel_task",
        ],
        permission_mode="bypassPermissions",
        mcp_servers={"nanoclaw": mcp_server},
        env=env,
    )

    response_parts: list[str] = []
    try:
        async for message in query(prompt=_make_prompt(prompt), options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.result:
                    response_parts.append(message.result)
    except Exception:
        if not response_parts:
            logger.exception("Task agent error")
            return "Task execution failed."
        logger.debug("Ignoring query cleanup error", exc_info=True)

    return "".join(response_parts) or "Task completed."
