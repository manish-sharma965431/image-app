from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import get_logger, setup_logging
from app.db.mongo import mongo
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import auth_routes, image_routes

settings = get_settings()
setup_logging(settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    await mongo.connect(settings.mongo_uri, settings.mongo_db)
    logger.info("%s started", settings.app_name)
    yield
    await mongo.close()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

# Middleware order: the LAST one added is the OUTERMOST (runs first).
# Request flow:  CORS -> Logging -> Auth -> route
# CORS outermost so even 401/500 responses carry CORS headers.
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time-ms"],
)

register_exception_handlers(app)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_routes.router)
api_v1.include_router(image_routes.router)
app.include_router(api_v1)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
