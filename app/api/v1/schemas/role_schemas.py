from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class PermissionSchema(BaseModel):
    id: UUID
    table_name: str
    read_access: bool
    write_access: bool
    update_access: bool
    delete_access: bool
    name: str

    class Config:
        from_attributes = True


class RoleCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class RoleUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)


class RoleResponseSchema(BaseModel):
    id: UUID
    name: str
    permissions: List[PermissionSchema]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleListResponseSchema(BaseModel):
    id: UUID
    name: str
    permission_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AddPermissionToRoleSchema(BaseModel):
    permission_id: UUID


class RemovePermissionFromRoleSchema(BaseModel):
    permission_id: UUID
