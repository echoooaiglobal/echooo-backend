from fastapi import APIRouter
from app.Http.Controllers import ClientController

router = APIRouter()
router.include_router(ClientController.router, prefix="/clients", tags=["Clients"])
