
import threading
import time

from fastapi.concurrency import run_in_threadpool
from PIL import Image

from app.core.config import get_settings
from app.core.exceptions import ModelUnavailableError
from app.core.logger import get_logger
from app.services.image_service import file_path

logger = get_logger(__name__)

# Display name (what your API returns)  ->  prompt text (what CLIP reads)
ROOM_LABELS = {
    "Bedroom": "a bedroom",
    "Kitchen": "a kitchen",
    "Drawing Area": "a living room",
    "Bathroom": "a bathroom",
    "Dining Room": "a dining room",
    "Balcony": "a balcony",
    "Study Room": "a home office",
    "Other": "something that is not a room",
}
PROMPT_TO_NAME = {prompt: name for name, prompt in ROOM_LABELS.items()}

_lock = threading.Lock()
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        with _lock:
            if _pipeline is None:
                name = get_settings().classifier_model
                try:
                    from transformers import pipeline

                    logger.info(
                        "Loading classifier '%s' (first run downloads it)", name
                    )
                    _pipeline = pipeline("zero-shot-image-classification", model=name)
                except Exception:
                    logger.exception("Could not load classifier '%s'", name)
                    raise ModelUnavailableError(
                        "Classification model could not be loaded"
                    )
    return _pipeline


def _run(path, top_k: int) -> list[dict]:
    pipe = _get_pipeline()
    with Image.open(path) as img:
        # the prediction happens on the next line
        results = pipe(img.convert("RGB"), candidate_labels=list(ROOM_LABELS.values()))
    results = sorted(results, key=lambda r: r["score"], reverse=True)[:top_k]
    return [
        {"label": PROMPT_TO_NAME[r["label"]], "score": round(float(r["score"]), 4)}
        for r in results
    ]


async def classify(filename: str, top_k: int) -> dict:
    path = file_path(filename)
    start = time.perf_counter()
    predictions = await run_in_threadpool(_run, path, top_k)
    logger.info(
        "Classified %s in %.0fms -> top: %s",
        filename,
        (time.perf_counter() - start) * 1000,
        predictions[0]["label"] if predictions else "-",
    )
    return {"model": get_settings().classifier_model, "predictions": predictions}
