"""Database operations for scheduled tasks.

Note: Message history is stored in conversations/ folder (not in DB).
The DB is only used for structured data that needs querying (scheduled tasks).
"""

import uuid
from datetime import datetime, timezone

import aiosqlite

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id TEXT PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    schedule_value TEXT NOT NULL,
    next_run TEXT,
    last_run TEXT,
    last_result TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON scheduled_tasks(status);

CREATE TABLE IF NOT EXISTS task_run_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    run_at TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    error TEXT,
    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_task_run_logs_task_id ON task_run_logs(task_id);
"""


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(_CREATE_TABLES)
        await db.commit()


# --- Task CRUD ---

async def create_task(db_path: str, chat_id: int, prompt: str, schedule_type: str, schedule_value: str, next_run: str) -> str:
    task_id = uuid.uuid4().hex[:8]
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO scheduled_tasks (id, chat_id, prompt, schedule_type, schedule_value, next_run, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, chat_id, prompt, schedule_type, schedule_value, next_run, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
    return task_id


async def get_all_tasks(db_path: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM scheduled_tasks")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_due_tasks(db_path: str) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM scheduled_tasks WHERE status = 'active' AND next_run <= ?",
            (now,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_task_status(db_path: str, task_id: str, status: str) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "UPDATE scheduled_tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def delete_task(db_path: str, task_id: str) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
        await db.commit()
        return cursor.rowcount > 0


async def update_task_after_run(db_path: str, task_id: str, last_result: str, next_run: str | None, status: str = "active") -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE scheduled_tasks SET last_run = ?, last_result = ?, next_run = ?, status = ? WHERE id = ?",
            (now, last_result, next_run, status, task_id),
        )
        await db.commit()


async def log_task_run(db_path: str, task_id: str, duration_ms: int, status: str, result: str | None = None, error: str | None = None) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO task_run_logs (task_id, run_at, duration_ms, status, result, error) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, datetime.now(timezone.utc).isoformat(), duration_ms, status, result, error),
        )
        await db.commit()
