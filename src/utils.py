import hashlib
from pathlib import Path

import structlog
from pdf2image import convert_from_path

logger = structlog.get_logger()


def calculate_file_hash(file_bytes: bytes) -> str:
    sha = hashlib.sha256()
    sha.update(file_bytes)
    return sha.hexdigest()


def convert_pdf_to_images(pdf_path: str, max_pages: int = 5) -> list[str]:
    """Converts PDF to list of temp image paths."""
    logger.debug("Converting PDF", path=pdf_path)
    try:
        images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=max_pages)
        image_paths = []
        base_path = Path(pdf_path).parent

        for i, img in enumerate(images):
            # Save as temp image
            img_path = base_path / f"{Path(pdf_path).stem}_page_{i}.jpg"
            img.save(img_path, "JPEG")
            image_paths.append(str(img_path))

        return image_paths
    except Exception as e:
        logger.error("PDF Conversion failed", error=str(e))
        raise
