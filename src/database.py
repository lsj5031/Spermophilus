import asyncio
import time
from pathlib import Path

import aiosqlite
import structlog

logger = structlog.get_logger()
DB_PATH = Path("data/ocr.db")

# Global event for worker hibernation
_job_available_event = asyncio.Event()


async def init_db() -> None:
    """Initialize tables for Jobs and Results."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Cache Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS results (
                file_hash TEXT PRIMARY KEY,
                parsed_text TEXT,
                created_at REAL
            )
        """)
        # Queue Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                file_hash TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
                worker_id TEXT,
                created_at REAL,
                started_at REAL
            )
        """)

        # Reset stuck jobs on startup (Crash Recovery)
        await db.execute("""
            UPDATE jobs 
            SET status = 'pending', worker_id = NULL, started_at = NULL 
            WHERE status = 'processing'
        """)
        await db.commit()
    logger.info("Database initialized and stuck jobs reset")


async def get_cached_text(file_hash: str) -> str | None:
    async with (
        aiosqlite.connect(DB_PATH) as db,
        db.execute(
            "SELECT parsed_text FROM results WHERE file_hash = ?", (file_hash,)
        ) as cursor,
    ):
        row = await cursor.fetchone()
        return row[0] if row else None


async def save_result(file_hash: str, text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO results (file_hash, parsed_text, created_at) "
            "VALUES (?, ?, ?)",
            (file_hash, text, time.time()),
        )
        await db.commit()


async def add_job(chat_id: int, message_id: int, file_hash: str, file_path: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO jobs (chat_id, message_id, file_hash, file_path, created_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (chat_id, message_id, file_hash, str(file_path), time.time()),
        )
        await db.commit()
        logger.info("Job added", chat_id=chat_id, file_hash=file_hash[:8])
        _job_available_event.set()  # Wake up sleeping worker
        return cursor.lastrowid or 0


async def claim_next_job(worker_id: str) -> dict | None:
    """Atomic claim using SQLite RETURNING clause."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            UPDATE jobs 
            SET status = 'processing', worker_id = ?, started_at = ?
            WHERE id = (
                SELECT id FROM jobs WHERE status = 'pending' 
                ORDER BY created_at ASC LIMIT 1
            )
            RETURNING id, chat_id, message_id, file_path, file_hash
        """,
            (worker_id, time.time()),
        )
        row = await cursor.fetchone()
        await db.commit()
        return dict(row) if row else None


async def mark_job_status(job_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        await db.commit()


def get_job_event():
    """Return the event for worker to listen on"""
    return _job_available_event


def reset_job_event():
    """Reset the job available event"""
    _job_available_event.clear()
