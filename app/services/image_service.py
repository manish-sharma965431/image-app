"""File-system + Pillow work. No HTTP, no DB here."""
import io
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, NotFoundError, UnsupportedMediaError
from app.core.logger import get_logger

logger = get_logger(__name__)

# Detected by Pillow from file content (never trust the client's filename/content-type)
FORMAT_TO_EXT = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def _storage() -> Path:
    path = get_settings().storage_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_url(filename: str) -> str:
    return f"{get_settings().cdn_base_url.rstrip('/')}/{filename}"


def file_path(filename: str) -> Path:
    path = (_storage() / filename).resolve()
    if _storage().resolve() not in path.parents or not path.exists():
        raise NotFoundError("Image file not found")
    return path


def _validate_and_detect(data: bytes) -> tuple[str, str]:
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            img.verify()
    except (UnidentifiedImageError, OSError):
        raise UnsupportedMediaError("File is not a valid image")
    if fmt not in FORMAT_TO_EXT:
        raise UnsupportedMediaError(f"Unsupported format. Allowed: {', '.join(FORMAT_TO_EXT)}")
    return FORMAT_TO_EXT[fmt], Image.MIME[fmt]


async def save_upload(file: UploadFile) -> dict:
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise FileTooLargeError(f"Max upload size is {get_settings().max_upload_mb} MB")
    if not data:
        raise UnsupportedMediaError("Empty file")

    ext, content_type = await run_in_threadpool(_validate_and_detect, data)
    filename = f"{uuid.uuid4().hex}{ext}"
    await run_in_threadpool((_storage() / filename).write_bytes, data)
    logger.info("Saved upload %s (%d bytes)", filename, len(data))
    return {"filename": filename, "image_url": build_url(filename),
            "content_type": content_type, "size_bytes": len(data)}


def _apply_text_watermark(src: Path, dest: Path, text: str, opacity: float) -> None:
    with Image.open(src) as img:
        base = img.convert("RGBA")
        overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        size = max(16, base.width // 20)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", size)
        except OSError:
            font = ImageFont.load_default(size=size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        margin = max(10, base.width // 50)
        x = base.width - (right - left) - margin - left
        y = base.height - (bottom - top) - margin - top
        draw.text((x, y), text, font=font, fill=(255, 255, 255, int(255 * opacity)))
        result = Image.alpha_composite(base, overlay)
        if dest.suffix == ".jpg":
            result = result.convert("RGB")
        result.save(dest)


async def add_watermark(filename: str, text: str, opacity: float) -> dict:
    src = file_path(filename)
    out_name = f"{src.stem}_wm{src.suffix}"
    dest = _storage() / out_name
    await run_in_threadpool(_apply_text_watermark, src, dest, text, opacity)
    logger.info("Watermarked %s -> %s", filename, out_name)
    return {"filename": out_name, "url": build_url(out_name)}


def delete_files(*filenames: str | None) -> None:
    for name in filenames:
        if name:
            (_storage() / name).unlink(missing_ok=True)
