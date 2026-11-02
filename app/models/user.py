from pymongo.errors import DuplicateKeyError

from app.core.exceptions import ConflictError
from app.core.utils import to_object_id, utcnow
from app.db.mongo import mongo


class UserModel:
    @staticmethod
    def _col():
        return mongo.db.users

    @classmethod
    async def create(cls, email: str, password_hash: str) -> dict:
        doc = {"email": email.lower(), "password_hash": password_hash, "created_at": utcnow()}
        try:
            result = await cls._col().insert_one(doc)
        except DuplicateKeyError:
            raise ConflictError("Email already registered")
        doc["_id"] = result.inserted_id
        return doc

    @classmethod
    async def find_by_email(cls, email: str) -> dict | None:
        return await cls._col().find_one({"email": email.lower()})

    @classmethod
    async def find_by_id(cls, user_id: str) -> dict | None:
        return await cls._col().find_one({"_id": to_object_id(user_id, "User")})
