from typing import Annotated
from fastapi import APIRouter, Depends
from app.schemas.user import User
from app.services.auth.auth import get_authenticated_user

router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@router.get("/me", response_model=User)
async def get_current_user(
    current_user: Annotated[User, Depends(get_authenticated_user)]
):
    """
    Obtiene la información del usuario actual autenticado
    """
    return current_user 