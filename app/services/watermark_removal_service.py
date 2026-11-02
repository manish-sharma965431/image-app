"""Watermark removal with OpenCV inpainting.
Inpainting = fill the masked pixels using the surrounding pixels.
Works well for small, simple watermarks on plain/smooth backgrounds; it can't
recover detail hidden under big or opaque logos."""

import time
from pathlib import Path

import cv2
import numpy as np
from fastapi.concurrency import run_in_threadpool

from app.core.exceptions import AppException
from app.core.logger import get_logger
from app.services.image_service import _storage, build_url, file_path

logger = get_logger(__name__)

PAD = 30  # extra pixels around the region, so inpainting has context to copy from

def _build_mask(
    crop: np.ndarray, box: tuple[int, int, int, int], mode: str
) -> np.ndarray:
    """Return a 0/255 mask the size of `crop`. 255 = pixels to repaint."""
    bx0, by0, bx1, by1 = box
    mask = np.zeros(crop.shape[:2], np.uint8)
    if mode == "box":
        mask[by0:by1, bx0:bx1] = 255  # repaint the whole rectangle
        return mask

    # "bright": repaint only the watermark strokes (light text/logo) inside the box.
    gray = cv2.cvtColor(crop[by0:by1, bx0:bx1], cv2.COLOR_BGR2GRAY)
    k = max(9, (min(gray.shape) // 3) | 1)  # structuring element, must be odd
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    tophat = cv2.morphologyEx(
        gray, cv2.MORPH_TOPHAT, kernel
    )  # keeps small bright shapes
    _, strokes = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    strokes = cv2.dilate(
        strokes, np.ones((3, 3), np.uint8), iterations=2
    )  # cover soft edges
    mask[by0:by1, bx0:bx1] = strokes
    return mask


def _remove(
    src: Path,
    dest: Path,
    x: int,
    y: int,
    w: int,
    h: int,
    mode: str,
    algorithm: str,
    radius: int,
) -> None:
    img = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if img is None:
        raise AppException("Could not read the image file")
    ih, iw = img.shape[:2]

    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(iw, x + w), min(ih, y + h)
    if x0 >= x1 or y0 >= y1:
        raise AppException(f"Region is outside the image (image is {iw}x{ih} px)")

    # work on a small crop around the region instead of the whole picture (faster)
    cx0, cy0, cx1, cy1 = (
        max(0, x0 - PAD),
        max(0, y0 - PAD),
        min(iw, x1 + PAD),
        min(ih, y1 + PAD),
    )
    crop = img[cy0:cy1, cx0:cx1].copy()
    box = (x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0)

    mask = _build_mask(crop, box, mode)
    flag = cv2.INPAINT_TELEA if algorithm == "telea" else cv2.INPAINT_NS
    img[cy0:cy1, cx0:cx1] = cv2.inpaint(crop, mask, radius, flag)

    params = [cv2.IMWRITE_JPEG_QUALITY, 95] if dest.suffix == ".jpg" else []
    if not cv2.imwrite(str(dest), img, params):
        raise AppException("Could not write the output image")


async def remove_watermark(
    filename: str,
    x: int,
    y: int,
    width: int,
    height: int,
    mode: str,
    algorithm: str,
    radius: int,
) -> dict:
    src = file_path(filename)
    out_name = f"{src.stem}_clean{src.suffix}"
    start = time.perf_counter()
    await run_in_threadpool(
        _remove,
        src,
        _storage() / out_name,
        x,
        y,
        width,
        height,
        mode,
        algorithm,
        radius,
    )
    logger.info(
        "Watermark removed %s -> %s (mode=%s, %.0fms)",
        filename,
        out_name,
        mode,
        (time.perf_counter() - start) * 1000,
    )
    return {
        "filename": out_name,
        "url": build_url(out_name),
        "mode": mode,
        "algorithm": algorithm,
        "region": {"x": x, "y": y, "width": width, "height": height},
    }
