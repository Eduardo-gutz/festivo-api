from pydantic import BaseModel
from typing import List

from app.modules.templates.schemas.template import Template, TemplateMinimal

class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    preview_image_url: str = ""
    is_premium: bool = False
    elements: list = []

class TemplateResponse(BaseModel):
    message: str
    template: Template


class TemplatesListResponse(BaseModel):
    message: str
    templates: List[TemplateMinimal]
    total: int