from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.models.user import User

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    # For MVP, return a dummy user
    # In production, this would decode JWT token and get user from database
    return User(
        username="admin",
        password="hashed_password",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        is_active=True
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user