from pymongo import AsyncMongoClient

from app.core.logger import get_logger

logger = get_logger(__name__)


class Mongo:
    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None
        self.db = None

    async def connect(self, uri: str, db_name: str) -> None:
        self.client = AsyncMongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        await self.client.admin.command("ping")  # fail fast if Mongo is down
        await self.db.users.create_index("email", unique=True)
        await self.db.images.create_index([("user_id", 1), ("created_at", -1)])
        logger.info("Connected to MongoDB: %s/%s", uri, db_name)

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            logger.info("MongoDB connection closed")


mongo = Mongo()
