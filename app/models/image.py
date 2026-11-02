from pymongo import ReturnDocument

from app.core.utils import to_object_id, utcnow
from app.db.mongo import mongo


class ImageModel:
    """One document per uploaded image. Only names/URLs/dates live in Mongo;
    the actual file lives in the local storage folder."""

    @staticmethod
    def _col():
        return mongo.db.images

    @classmethod
    async def create(
        cls,
        *,
        user_id: str,
        original_name: str,
        filename: str,
        image_url: str,
        content_type: str,
        size_bytes: int,
    ) -> dict:
        doc = {
            "user_id": user_id,
            "original_name": original_name,
            "filename": filename,  # name of file inside storage folder
            "image_url": image_url,  # CDN base URL + filename
            "content_type": content_type,
            "size_bytes": size_bytes,
            "status": "uploaded",
            "created_at": utcnow(),
            "processed_at": None,
            "processed_filename": None,
            "processed_url": None,
            "classification": None,
            "watermark_removal": None,
        }
        result = await cls._col().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    async def find_owned(cls, image_id: str, user_id: str) -> dict | None:
        return await cls._col().find_one(
            {"_id": to_object_id(image_id, "Image"), "user_id": user_id}
        )

    @classmethod
    async def list_by_user(
        cls, user_id: str, skip: int, limit: int
    ) -> tuple[list[dict], int]:
        query = {"user_id": user_id}
        cursor = cls._col().find(query).sort("created_at", -1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        total = await cls._col().count_documents(query)
        return items, total

    @classmethod
    async def mark_processed(
        cls, image_id, processed_filename: str, processed_url: str
    ) -> dict:
        return await cls._col().find_one_and_update(
            {"_id": image_id},
            {
                "$set": {
                    "status": "processed",
                    "processed_at": utcnow(),
                    "processed_filename": processed_filename,
                    "processed_url": processed_url,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

    @classmethod
    async def delete(cls, image_id) -> None:
        await cls._col().delete_one({"_id": image_id})

    @classmethod
    async def save_classification(cls, image_id, result: dict) -> dict:
        return await cls._col().find_one_and_update(
            {"_id": image_id},
            {"$set": {"classification": {**result, "classified_at": utcnow()}}},
            return_document=ReturnDocument.AFTER,
        )
    
    @classmethod
    async def save_watermark_removal(cls, image_id, result: dict) -> dict:
        return await cls._col().find_one_and_update(
            {"_id": image_id},
            {"$set": {"watermark_removal": {**result, "removed_at": utcnow()}}},
            return_document=ReturnDocument.AFTER,
        )
