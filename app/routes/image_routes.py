from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, Response

from app.controllers import image_controller
from app.dependencies import get_current_user
from app.schemas.image import ImageListResponse, ImageResponse, WatermarkRequest, RemoveWatermarkRequest

router = APIRouter(
    prefix="/images", tags=["Images"], dependencies=[Depends(get_current_user)]
)


@router.post("", response_model=ImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...), user: dict = Depends(get_current_user)
):
    return await image_controller.upload(user, file)


@router.get("", response_model=ImageListResponse)
async def list_images(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    return await image_controller.list_images(user, skip, limit)


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str, user: dict = Depends(get_current_user)):
    return await image_controller.get_image(user, image_id)


@router.get("/{image_id}/file")
async def get_image_file(
    image_id: str,
    variant: Literal["original", "processed"] = "original",
    user: dict = Depends(get_current_user),
):
    return FileResponse(await image_controller.get_file_path(user, image_id, variant))


@router.post("/{image_id}/watermark", response_model=ImageResponse)
async def add_watermark(
    image_id: str, payload: WatermarkRequest, user: dict = Depends(get_current_user)
):
    return await image_controller.watermark(user, image_id, payload)


@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: str, user: dict = Depends(get_current_user)):
    await image_controller.delete(user, image_id)
    return Response(status_code=204)


@router.post("/{image_id}/classify", response_model=ImageResponse)
async def classify_image(
    image_id: str,
    top_k: int = Query(5, ge=1, le=10),
    user: dict = Depends(get_current_user),
):
    return await image_controller.classify(user, image_id, top_k)


@router.post("/{image_id}/remove-watermark", response_model=ImageResponse)
async def remove_watermark(
    image_id: str,
    payload: RemoveWatermarkRequest,
    user: dict = Depends(get_current_user),
):
    return await image_controller.remove_watermark(user, image_id, payload)
