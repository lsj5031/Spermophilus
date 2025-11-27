import asyncio
import os

import structlog
from openai import AsyncOpenAI
from telegram.ext import Application

from .database import claim_next_job, mark_job_status, save_result
from .utils import convert_pdf_to_images

logger = structlog.get_logger()


class OCRWorker:
    def __init__(self, app: Application, worker_id: str, api_url: str):
        self.app = app
        self.worker_id = worker_id
        # Initialize OpenAI Client for LM Studio
        self.client = AsyncOpenAI(base_url=api_url, api_key="lm-studio")
        self.running = True

    async def is_api_healthy(self) -> bool:
        try:
            # Quick lightweight call to check if server is up
            await self.client.models.list()
            return True
        except Exception:
            return False

    async def extract_text_from_image(self, image_path: str) -> str:
        # Specific prompt for OCR
        import base64

        with open(image_path, "rb") as img_file:
            b64_image = base64.b64encode(img_file.read()).decode("utf-8")

        response = await self.client.chat.completions.create(
            model="local-model",  # LM Studio ignores model name usually
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all text from this image strictly. "
                                "No commentary."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                        },
                    ],
                }
            ],
            temperature=0.0,
            timeout=600,
        )
        return (
            response.choices[0].message.content.strip()
            if response.choices[0].message.content
            else ""
        )

    async def process_job(self, job: dict):
        log = logger.bind(job_id=job["id"], file_hash=job["file_hash"])
        log.info("Starting processing")

        file_path = job["file_path"]
        extracted_text = ""

        try:
            # Determine File Type
            if file_path.endswith(".pdf"):
                image_paths = await asyncio.to_thread(convert_pdf_to_images, file_path)
                full_text = []
                for img in image_paths:
                    text = await self.extract_text_from_image(img)
                    full_text.append(text)
                    os.remove(img)  # Cleanup temp page
                extracted_text = "\n\n--- Page Break ---\n\n".join(full_text)
            else:
                extracted_text = await self.extract_text_from_image(file_path)

            # Save & Notify
            await save_result(job["file_hash"], extracted_text)
            
            # Send to external API (if configured)
            api_endpoint = os.getenv("RESULTS_API_ENDPOINT")
            if api_endpoint:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            api_endpoint,
                            json={
                                "file_hash": job["file_hash"],
                                "extracted_text": extracted_text,
                                "worker_id": self.worker_id,
                            },
                            timeout=600,
                        )
                    log.info("Result sent to API", endpoint=api_endpoint)
                except Exception as api_error:
                    log.warning("Failed to send to API", error=str(api_error))

            # Send Reply
            # Split message if too long (Telegram limit 4096)
            chunks = [
                extracted_text[i : i + 4000]
                for i in range(0, len(extracted_text), 4000)
            ]
            for chunk in chunks:
                await self.app.bot.send_message(
                    chat_id=job["chat_id"],
                    text=f"✅ <b>OCR Result:</b>\n\n{chunk}",
                    reply_to_message_id=job["message_id"],
                    parse_mode="HTML",
                )

            await mark_job_status(job["id"], "completed")
            log.info("Job completed")

            # Remove original file
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            log.error("Job failed", error=str(e))
            await mark_job_status(job["id"], "failed")
            await self.app.bot.send_message(
                chat_id=job["chat_id"],
                text="❌ Processing failed. Please check the file and try again.",
                reply_to_message_id=job["message_id"],
            )

    async def run(self):
        logger.info("Worker started", worker_id=self.worker_id)
        while self.running:
            try:
                # 1. Check API Health
                if not await self.is_api_healthy():
                    logger.warning(
                        "OCR API unavailable. Waiting...", worker_id=self.worker_id
                    )
                    await asyncio.sleep(10)
                    continue

                # 2. Claim Job
                job = await claim_next_job(self.worker_id)
                if not job:
                    await asyncio.sleep(1)  # Idle
                    continue

                # 3. Process
                await self.process_job(job)

            except Exception as e:
                logger.error("Worker loop crash", error=str(e))
                await asyncio.sleep(5)
