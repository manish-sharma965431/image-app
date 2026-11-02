from fastapi.concurrency import run_in_threadpool

from app.core.exceptions import UnauthorizedError
from app.core.logger import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import UserModel
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

logger = get_logger(__name__)


async def register(payload: RegisterRequest) -> UserResponse:
    hashed = await run_in_threadpool(hash_password, payload.password)  # bcrypt is CPU-heavy
    user = await UserModel.create(payload.email, hashed)
    logger.info("User registered: %s", user["email"])
    return UserResponse.from_doc(user)


async def login(payload: LoginRequest) -> TokenResponse:
    user = await UserModel.find_by_email(payload.email)
    # Same message for "no user" and "wrong password" => no account enumeration
    if not user or not await run_in_threadpool(verify_password, payload.password, user["password_hash"]):
        logger.warning("Failed login for %s", payload.email)
        raise UnauthorizedError("Invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user["_id"])))
