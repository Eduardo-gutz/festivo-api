import time
from typing import Annotated, List, Optional
from fastapi import Depends, HTTPException, status
from pymongo.collection import Collection as AsyncCollection
from bson import ObjectId

from app.db.db import get_collection
from app.modules.templates.schemas.template import Template, TemplateMinimal
from app.db.objectIdMongo import PyObjectId
from app.core.utils.error_codes import ErrorCodes
from app.modules.user.schemas.user import User, UserMinimal


class TemplateService:
    def __init__(self, templates: Annotated[AsyncCollection, Depends(get_collection('templates'))]):
        self.templates = templates

    async def create_template(self, template_data: dict, user_id: str) -> Template:
        if not template_data.get("name", "").strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCodes.INVALID_DATA
            )

        existing_template = await self.templates.find_one({"name": template_data["name"]})
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCodes.TEMPLATE_ALREADY_EXISTS
            )

        current_time = int(time.time())
        db_template = {
            "name": template_data["name"],
            "description": template_data.get("description", ""),
            "preview_image_url": template_data.get("preview_image_url", ""),
            "is_premium": template_data.get("is_premium", False),
            "created_at": current_time,
            "updated_at": current_time,
            "elements": template_data.get("elements", []),
            "user_id": user_id
        }

        result = await self.templates.insert_one(db_template)
        db_template["_id"] = result.inserted_id

        template_cursor = await self.templates.aggregate([
            {
                "$match": {"_id": result.inserted_id}
            },
            {"$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }},
            {"$unwind": "$user"}
        ])
        template = await template_cursor.to_list(length=1)

        return Template.model_validate(template[0])


    async def get_templates(self, skip: int = 0, limit: int = 100, is_premium: Optional[bool] = None) -> List[TemplateMinimal]:
        query = {}
        if is_premium is not None:
            query["is_premium"] = is_premium

        cursor = self.templates.find(query).skip(skip).limit(limit)
        templates = await cursor.to_list(length=limit)

        return [TemplateMinimal.model_validate(template) for template in templates]

    async def get_template_by_id(self, template_id: str) -> Template:
        try:
            object_id = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCodes.INVALID_DATA
            )

        template = await self.templates.find_one({"_id": object_id})
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCodes.TEMPLATE_NOT_FOUND
            )

        return Template.model_validate(template)

    async def update_template(self, template_id: str, update_data: dict, user_auth: User) -> Template:
        try:
            object_id = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCodes.INVALID_DATA
            )

        existing_template = await self.templates.find_one({"_id": object_id})
        if not existing_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCodes.TEMPLATE_NOT_FOUND
            )
            
        if existing_template["user_id"] != user_auth.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCodes.NOT_AUTHORIZED
            )

        if "name" in update_data and update_data["name"] != existing_template["name"]:
            name_exists = await self.templates.find_one({
                "name": update_data["name"],
                "_id": {"$ne": object_id}
            })
            if name_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=ErrorCodes.TEMPLATE_ALREADY_EXISTS
                )

        update_data["updated_at"] = int(time.time())

        await self.templates.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

        updated_template = await self.templates.find_one({"_id": object_id})
        return Template.model_validate(updated_template)

    async def delete_template(self, template_id: str, user_auth: User) -> bool:
        try:
            object_id = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCodes.INVALID_DATA
            )

        existing_template = await self.templates.find_one({"_id": object_id})
        if not existing_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCodes.TEMPLATE_NOT_FOUND
            )

        if existing_template["user_id"] != user_auth.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCodes.NOT_AUTHORIZED
            )

        result = await self.templates.delete_one({"_id": object_id})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCodes.TEMPLATE_NOT_FOUND
            )

        return True

    async def get_templates_by_premium_status(self, is_premium: bool) -> List[TemplateMinimal]:
        cursor = self.templates.find({"is_premium": is_premium})
        templates = await cursor.to_list(length=None)

        return [TemplateMinimal.model_validate(template) for template in templates]

    async def search_templates_by_name(self, search_term: str) -> List[TemplateMinimal]:
        query = {
            "name": {
                "$regex": search_term,
                "$options": "i"
            }
        }

        cursor = self.templates.find(query)
        templates = await cursor.to_list(length=None)

        return [TemplateMinimal.model_validate(template) for template in templates]


def get_template_service(
    templates: Annotated[AsyncCollection, Depends(get_collection('templates'))]
) -> TemplateService:
    return TemplateService(templates)
