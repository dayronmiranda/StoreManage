from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId

from app.models.user import User
from app.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse,
    UserLogin
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.core.security import get_password_hash
from app.utils.validators import validate_email

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name, last name or username"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List users with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if search:
        query_params["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    if active is not None:
        query_params["is_active"] = active
    
    # Get total
    total_users = await User.find(query_params).count()
    
    # Get paginated users
    skip = (pagination.page - 1) * pagination.size
    user_list = await User.find(query_params).skip(skip).limit(pagination.size).to_list()
    
    # Convert to response
    user_responses = [
        UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            roles=user.roles,
            allowed_warehouses=user.allowed_warehouses,
            created_at=user.created_at,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts
        )
        for user in user_list
    ]
    
    total_pages = (total_users + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=user_responses,
        total=total_users,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new user"""
    
    # Validate email
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Verify that username does not exist
    existing_user = await User.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Verify that email does not exist
    existing_email = await User.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        password=get_password_hash(user_data.password),
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active,
        roles=user_data.roles,
        allowed_warehouses=user_data.allowed_warehouses
    )
    
    await user.insert()
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=user.roles,
        allowed_warehouses=user.allowed_warehouses,
        created_at=user.created_at,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID"""
    
    try:
        user = await User.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=user.roles,
        allowed_warehouses=user.allowed_warehouses,
        created_at=user.created_at,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update user"""
    
    try:
        user = await User.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate email if provided
    if user_data.email and not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Verify that email does not exist in another user
    if user_data.email and user_data.email != user.email:
        existing_email = await User.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await user.save()
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        roles=user.roles,
        allowed_warehouses=user.allowed_warehouses,
        created_at=user.created_at,
        last_login=user.last_login,
        failed_login_attempts=user.failed_login_attempts
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete user (deactivate)"""
    
    try:
        user = await User.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Do not allow deleting your own user
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own user"
        )
    
    # Deactivate user instead of deleting
    user.is_active = False
    await user.save()
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user)
):
    """Reset user password"""
    
    try:
        user = await User.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate password length
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Update password
    user.password = get_password_hash(new_password)
    user.failed_login_attempts = 0
    await user.save()
    
    return {"message": "Password updated successfully"}


@router.post("/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Activate/deactivate user"""
    
    try:
        user = await User.get(PydanticObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Do not allow deactivating your own user
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own user"
        )
    
    # Change status
    user.is_active = not user.is_active
    if user.is_active:
        user.failed_login_attempts = 0
    
    await user.save()
    
    status_str = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status_str} successfully"}
