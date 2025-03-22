from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from app.Http.Controllers.AuthController import auth_backend, fastapi_users, User

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
router.include_router(
    fastapi_users.get_register_router(User), prefix="/auth", tags=["auth"]
)
