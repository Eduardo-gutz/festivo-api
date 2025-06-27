from typing import Annotated
from fastapi import APIRouter, Depends, Security
from app.modules.user.schemas.user import User
from app.modules.auth.services.auth import get_authenticated_user

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