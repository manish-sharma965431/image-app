from fastapi import Depends, Request
from fastapi.security import HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.models.user import UserModel

# auto_error=False: the middleware already enforces auth. This only adds the
# "Authorize" button to Swagger UI (/docs).
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(request: Request, _=Depends(bearer_scheme)) -> dict:
    user_id = getattr(request.state, "user_id", None)
    user = await UserModel.find_by_id(user_id) if user_id else None
    if not user:
        raise UnauthorizedError("User no longer exists")
    return user
