"""
Role router with service layer
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from uuid import UUID
import logging

from app.api.v1.schemas.role_schemas import (
    RoleCreateSchema,
    RoleUpdateSchema,
    RoleResponseSchema,
    RoleListResponseSchema,
    AddPermissionToRoleSchema,
)
from app.core.services.role_service import RoleService
from app.config.dependencies import get_role_service
from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])
logger = logging.getLogger(__name__)


def _check_admin_access(current_user: dict) -> None:
    """
    Helper function to check if user has admin access

    Raises:
        HTTPException: If user is not admin
    """
    if current_user["role"] != "admin":
        logger.warning(
            f"⚠️  Unauthorized access attempt by user: {current_user['user_id']}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )


@router.post(
    "/",
    response_model=RoleResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    request: RoleCreateSchema,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Create a new role (admin only)"""

    # Authorization check
    _check_admin_access(current_user)

    try:
        role = await role_service.create_role(name=request.name)
        logger.info(f"✅ Role created: {role.id}")
        return RoleResponseSchema.from_orm(role)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to create role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role",
        )


@router.get(
    "/",
    response_model=List[RoleListResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Get all roles with pagination"""

    try:
        roles = await role_service.get_all_roles(skip=skip, limit=limit)
        return [
            RoleListResponseSchema(
                id=r.id,
                name=r.name.value if hasattr(r.name, "value") else r.name,
                permission_count=len(r.permissions),
                created_at=r.created_at,
            )
            for r in roles
        ]

    except Exception as e:
        logger.error(f"❌ Failed to list roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles",
        )


@router.get(
    "/{role_id}",
    response_model=RoleResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_role_by_id(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Get role by ID with all permissions"""

    try:
        role = await role_service.get_role_by_id(role_id=role_id)
        return RoleResponseSchema.from_orm(role)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve role",
        )


@router.patch(
    "/{role_id}",
    response_model=RoleResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_role(
    role_id: UUID,
    request: RoleUpdateSchema,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Update role (admin only)"""

    # Authorization check
    _check_admin_access(current_user)

    try:
        role = await role_service.update_role(
            role_id=role_id,
            name=request.name,
        )
        logger.info(f"✅ Role updated: {role_id}")
        return RoleResponseSchema.from_orm(role)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to update role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role",
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Delete role (admin only)"""

    # Authorization check
    _check_admin_access(current_user)

    try:
        await role_service.delete_role(role_id=role_id)
        logger.info(f"✅ Role deleted: {role_id}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to delete role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role",
        )


@router.post("/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def add_permission_to_role(
    role_id: UUID,
    request: AddPermissionToRoleSchema,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Add permission to role (admin only)"""

    # Authorization check
    _check_admin_access(current_user)

    try:
        await role_service.add_permission_to_role(
            role_id=role_id,
            permission_id=request.permission_id,
        )
        logger.info(f"✅ Permission {request.permission_id} added to role {role_id}")

        return {"message": "Permission added to role successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to add permission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add permission to role",
        )


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_200_OK,
)
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    current_user: dict = Depends(get_current_user),
):
    """Remove permission from role (admin only)"""

    # Authorization check
    _check_admin_access(current_user)

    try:
        await role_service.remove_permission_from_role(
            role_id=role_id,
            permission_id=permission_id,
        )
        logger.info(f"✅ Permission {permission_id} removed from role {role_id}")

        return {"message": "Permission removed from role successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to remove permission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove permission from role",
        )
