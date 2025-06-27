from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, Security
from pydantic import BaseModel

from app.modules.templates.schemas.template import Template, TemplateMinimal, TemplateUpdate
from app.modules.templates.services.templates import TemplateService, get_template_service
from app.modules.auth.services.auth import get_authenticated_user
from app.modules.user.schemas.user import User, Role
from app.core.utils.error_codes import ErrorCodes
from app.modules.templates.moodels.templateResponse import TemplateResponse, TemplatesListResponse, TemplateCreate

router = APIRouter(
    prefix="/templates",
    tags=["templates"]
)



@router.post("/", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    template_service: Annotated[TemplateService, Depends(get_template_service)],
    current_user: Annotated[User, Security(
        get_authenticated_user, scopes=["publisher", "admin"])]
):
    template = await template_service.create_template(template_data.model_dump(), current_user.id)
    return TemplateResponse(
        message="Template created successfully",
        template=template
    )


@router.get("/", response_model=TemplatesListResponse)
async def get_templates(
    template_service: Annotated[TemplateService, Depends(get_template_service)],
    skip: int = 0,
    limit: int = 100,
    is_premium: Optional[bool] = None
):
    templates = await template_service.get_templates(skip=skip, limit=limit, is_premium=is_premium)
    return TemplatesListResponse(
        message="Templates obtained successfully",
        templates=templates,
        total=len(templates)
    )


@router.get("/search", response_model=TemplatesListResponse)
async def search_templates(
    template_service: Annotated[TemplateService, Depends(get_template_service)],
    q: str
):
    templates = await template_service.search_templates_by_name(q)
    return TemplatesListResponse(
        message=f"Search completed for: '{q}'",
        templates=templates,
        total=len(templates)
    )


@router.get("/premium", response_model=TemplatesListResponse)
async def get_premium_templates(
    template_service: Annotated[TemplateService, Depends(get_template_service)]
):
    templates = await template_service.get_templates_by_premium_status(is_premium=True)
    return TemplatesListResponse(
        message="Premium templates obtained successfully",
        templates=templates,
        total=len(templates)
    )


@router.get("/free", response_model=TemplatesListResponse)
async def get_free_templates(
    template_service: Annotated[TemplateService, Depends(get_template_service)]
):
    templates = await template_service.get_templates_by_premium_status(is_premium=False)
    return TemplatesListResponse(
        message="Free templates obtained successfully",
        templates=templates,
        total=len(templates)
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    template_service: Annotated[TemplateService, Depends(get_template_service)]
):
    template = await template_service.get_template_by_id(template_id)
    return TemplateResponse(
        message="Template obtained successfully",
        template=template
    )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    template_service: Annotated[TemplateService, Depends(get_template_service)],
    current_user: Annotated[User, Security(
        get_authenticated_user, scopes=["publisher", "admin"])]
):
    update_data = {k: v for k, v in template_data.model_dump().items()
                   if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail=ErrorCodes.INVALID_DATA
        )

    template = await template_service.update_template(template_id, update_data, current_user)
    return TemplateResponse(
        message="Template updated successfully",
        template=template
    )


@router.patch("/{template_id}/elements", response_model=TemplateResponse)
async def update_template_elements(
    template_id: str,
    template_service: Annotated[TemplateService, Depends(get_template_service)],
    current_user: Annotated[User, Security(
        get_authenticated_user, scopes=["publisher", "admin"])],
    elements: List = Body(..., description="Nuevos elementos del template")
):
    template = await template_service.update_template(template_id, {"elements": elements}, current_user)
    return TemplateResponse(
        message="Template elements updated successfully",
        template=template
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    template_service: Annotated[TemplateService, Depends(get_template_service)],
    current_user: Annotated[User, Security(
        get_authenticated_user, scopes=["publisher", "admin"])]
):
    await template_service.delete_template(template_id, current_user)
    return {"message": "Template deleted successfully"}
