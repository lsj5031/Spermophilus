import os
from pathlib import Path

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from .database import add_job, get_cached_text
from .utils import calculate_file_hash

logger = structlog.get_logger()
TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_USERS_STR = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USERS = set(map(int, ALLOWED_USERS_STR.split(","))) if ALLOWED_USERS_STR else set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("👋 Send me an Image or PDF to extract text.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("handle_document called")
    if not update.message or not update.effective_user:
        logger.warning("No message or user")
        return

    user_id = update.effective_user.id
    logger.info("Received message", user_id=user_id, has_document=bool(update.message.document), has_photo=bool(update.message.photo))

    # Auth Check
    if user_id not in ALLOWED_USERS:
        logger.warning("Unauthorized access attempt", user_id=user_id, allowed_users=ALLOWED_USERS)
        return

    # Get File
    msg = update.message
    file_obj = await (msg.document or msg.photo[-1]).get_file()

    # Download to memory
    file_bytes = await file_obj.download_as_bytearray()

    # Hash
    file_hash = calculate_file_hash(file_bytes)

    # 1. Deduplication (Cache)
    cached_text = await get_cached_text(file_hash)
    if cached_text:
        logger.info("Cache hit", file_hash=file_hash[:8])
        await msg.reply_text(
            f"{cached_text[:4000]}\n\n(⚡ Cached Result)",
            reply_to_message_id=msg.message_id,
        )
        return

    # 2. Save & Queue
    file_ext = (
        ".pdf"
        if msg.document and msg.document.mime_type and "pdf" in msg.document.mime_type
        else ".jpg"
    )
    save_path = TEMP_DIR / f"{file_hash}{file_ext}"

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    await add_job(msg.chat_id, msg.message_id, file_hash, str(save_path))

    await msg.reply_text(
        "⏳ Queued for processing...", reply_to_message_id=msg.message_id
    )
