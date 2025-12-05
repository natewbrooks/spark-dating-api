from pydantic import BaseModel, field_validator
from .moderation_status import ModerationStatusEnum 
from uuid import UUID
from typing import Optional

class PhotoMetadataSchema(BaseModel):
    moderation_status: Optional[ModerationStatusEnum] = ModerationStatusEnum.pending
    slot: Optional[int] = None
    is_primary: Optional[bool] = None

    @field_validator("slot")
    @classmethod
    def lock_slot_range(cls, v: Optional[int]):
        # Skip validation if slot isn't provided
        if v is None:
            return v
        if not (1 <= v <= 6):
            raise ValueError("Slot must be between 1 and 6")
        return v

    @field_validator("moderation_status", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class PhotoMetaSchema(BaseModel):
    id: UUID
    path: str
    url: str
    size_bytes: int
    mime_type: str
    metadata: PhotoMetadataSchema

class PhotoSchema(BaseModel):
    id: UUID
    path: str

class UpdatePhotoMetaSchema(BaseModel):
    photo: PhotoSchema
    metadata: PhotoMetadataSchema