from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WatermarkRequest(BaseModel):
    text: str = Field(min_length=1, max_length=60)
    opacity: float = Field(default=0.6, ge=0.05, le=1.0)


class RemoveWatermarkRequest(BaseModel):
    # rectangle that covers the watermark, in pixels from the image's top-left corner
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(ge=1, le=10000)
    height: int = Field(ge=1, le=10000)
    mode: Literal["box", "bright"] = (
        "bright"  # bright = repaint only light strokes; box = whole rectangle
    )
    algorithm: Literal["telea", "ns"] = "telea"
    radius: int = Field(default=5, ge=1, le=25)
    confirm_ownership: bool = (
        False  # must be true: you own the image or have permission
    )


class Prediction(BaseModel):
    label: str
    score: float


class ClassificationResult(BaseModel):
    model: str
    predictions: list[Prediction]
    classified_at: datetime


class WatermarkRemovalResult(BaseModel):
    filename: str
    url: str
    mode: str
    algorithm: str
    region: dict[str, int]
    removed_at: datetime


class ImageResponse(BaseModel):
    id: str
    original_name: str
    filename: str
    image_url: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime
    processed_at: datetime | None = None
    processed_filename: str | None = None
    processed_url: str | None = None
    classification: ClassificationResult | None = None
    watermark_removal: WatermarkRemovalResult | None = None

    @classmethod
    def from_doc(cls, doc: dict) -> "ImageResponse":
        return cls.model_validate({**doc, "id": str(doc["_id"])})


class ImageListResponse(BaseModel):
    items: list[ImageResponse]
    total: int
    skip: int
    limit: int
