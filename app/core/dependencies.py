from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_token
from app.models.user import User
from app.schemas.user import UserResponse

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception
    
    # Find user in database
    user = await User.get(user_id)
    if user is None:
        raise credentials_exception
    
    # Verify user is active
    if not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.isActive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """Get current user (optional, for public endpoints)"""
    if not token:
        return None
    
    try:
        user_id = verify_token(token)
        if user_id is None:
            return None
        
        user = await User.get(user_id)
        if user is None or not user.isActive:
            return None
            
        return user
    except:
        return None


def require_permission(permission: str):
    """Decorator to require specific permissions"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        # TODO: Implement permission logic when roles are implemented
        # For now, just verify user is authenticated
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return permission_checker


def require_warehouse_access(warehouse_id: str):
    """Decorator to require access to a specific warehouse"""
    async def warehouse_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        # If user doesn't have specific warehouses, has access to all
        if not current_user.allowed_warehouses:
            return current_user
        
        # Check if has access to specific warehouse
        if warehouse_id not in current_user.allowed_warehouses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this warehouse"
            )
        
        return current_user
    
    return warehouse_checker


class PermissionChecker:
    """Class to verify permissions in a more flexible way"""
    
    def __init__(self, required_permissions: list):
        self.required_permissions = required_permissions
    
    async def __call__(self, current_user: User = Depends(get_current_active_user)):
        # TODO: Implement real permission verification
        # For now just verify authentication
        return current_user