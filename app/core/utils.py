from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from app.core.exceptions import NotFoundError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_object_id(value: str, label: str = "Resource") -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise NotFoundError(f"{label} not found")
