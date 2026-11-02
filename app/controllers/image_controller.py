from pathlib import Path

from fastapi import UploadFile

from app.models.image import ImageModel
from app.core.exceptions import AppException, NotFoundError
from app.schemas.image import (
    ImageListResponse,
    ImageResponse,
    RemoveWatermarkRequest,
    WatermarkRequest,
)
from app.services import classify_service, image_service, watermark_removal_service


async def _get_owned(user: dict, image_id: str) -> dict:
    doc = await ImageModel.find_owned(image_id, str(user["_id"]))
    if not doc:  # 404 (not 403) so users can't probe other people's IDs
        raise NotFoundError("Image not found")
    return doc


async def upload(user: dict, file: UploadFile) -> ImageResponse:
    saved = await image_service.save_upload(file)
    try:
        doc = await ImageModel.create(
            user_id=str(user["_id"]), original_name=file.filename or "unnamed", **saved
        )
    except Exception:
        image_service.delete_files(saved["filename"])  # don't leave orphan files
        raise
    return ImageResponse.from_doc(doc)


async def list_images(user: dict, skip: int, limit: int) -> ImageListResponse:
    items, total = await ImageModel.list_by_user(str(user["_id"]), skip, limit)
    return ImageListResponse(
        items=[ImageResponse.from_doc(i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )


async def get_image(user: dict, image_id: str) -> ImageResponse:
    return ImageResponse.from_doc(await _get_owned(user, image_id))


async def watermark(
    user: dict, image_id: str, payload: WatermarkRequest
) -> ImageResponse:
    doc = await _get_owned(user, image_id)
    result = await image_service.add_watermark(
        doc["filename"], payload.text, payload.opacity
    )
    updated = await ImageModel.mark_processed(
        doc["_id"], result["filename"], result["url"]
    )
    return ImageResponse.from_doc(updated)


async def get_file_path(user: dict, image_id: str, variant: str) -> Path:
    doc = await _get_owned(user, image_id)
    name = doc["processed_filename"] if variant == "processed" else doc["filename"]
    if not name:
        raise NotFoundError("Image has not been processed yet")
    return image_service.file_path(name)


async def delete(user: dict, image_id: str) -> None:
    doc = await _get_owned(user, image_id)
    await ImageModel.delete(doc["_id"])
    image_service.delete_files(doc["filename"], doc["processed_filename"])


async def classify(user: dict, image_id: str, top_k: int) -> ImageResponse:
    doc = await _get_owned(user, image_id)
    result = await classify_service.classify(doc["filename"], top_k)
    print(result)
    updated = await ImageModel.save_classification(doc["_id"], result)
    return ImageResponse.from_doc(updated)


async def remove_watermark(
    user: dict, image_id: str, payload: RemoveWatermarkRequest
) -> ImageResponse:
    if not payload.confirm_ownership:
        raise AppException(
            "Set confirm_ownership to true: only edit images you own or have permission to edit"
        )
    doc = await _get_owned(user, image_id)
    result = await watermark_removal_service.remove_watermark(
        doc["filename"],
        payload.x,
        payload.y,
        payload.width,
        payload.height,
        payload.mode,
        payload.algorithm,
        payload.radius,
    )
    updated = await ImageModel.save_watermark_removal(doc["_id"], result)
    return ImageResponse.from_doc(updated)
