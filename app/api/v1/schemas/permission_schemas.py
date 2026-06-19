from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class PermissionCreateSchema(BaseModel):
    table_name: str = Field(..., min_length=1, max_length=120)
    read_access: bool = False
    write_access: bool = False
    update_access: bool = False
    delete_access: bool = False


class PermissionUpdateSchema(BaseModel):
    table_name: Optional[str] = Field(None, min_length=1, max_length=120)
    read_access: Optional[bool] = None
    write_access: Optional[bool] = None
    update_access: Optional[bool] = None
    delete_access: Optional[bool] = None


class PermissionResponseSchema(BaseModel):
    id: UUID
    table_name: str
    read_access: bool
    write_access: bool
    update_access: bool
    delete_access: bool
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionListResponseSchema(BaseModel):
    id: UUID
    table_name: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
