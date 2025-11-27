import asyncio
import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from .database import init_db
from .handlers import handle_document, start
from .logger import setup_logging
from .worker import OCRWorker

load_dotenv()
setup_logging(os.getenv("LOG_LEVEL", "INFO"))


async def post_init(app):
    """Lifecycle hook: Starts DB and Workers."""
    await init_db()

    worker = OCRWorker(
        app=app,
        worker_id=os.getenv("WORKER_NAME", "worker_1"),
        api_url=os.getenv("LM_STUDIO_URL"),
    )
    # Run worker in background
    asyncio.create_task(worker.run())


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing")

    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.Document.ALL | filters.PHOTO, handle_document)
    )

    print("🚀 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
