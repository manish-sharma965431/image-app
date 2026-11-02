from fastapi import APIRouter, Depends

from app.controllers import auth_controller
from app.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest):
    return await auth_controller.register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    return await auth_controller.login(payload)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse.from_doc(user)
