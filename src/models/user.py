from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, List
from pymongo import IndexModel


class User(Document):
    username: Indexed(str, unique=True)
    password: str  # plain text for MVP
    email: Indexed(str, unique=True)  # simplified from EmailStr
    first_name: str
    last_name: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    roles: List[str] = []  # Role IDs
    allowed_warehouses: List[str] = []  # Warehouse IDs

    class Settings:
        collection = "users"
        indexes = [
            IndexModel([("username", 1)], unique=True),
            IndexModel([("email", 1)], unique=True),
            IndexModel([("is_active", 1)]),
        ]


class Token(Document):
    user_id: str
    token: Indexed(str, unique=True)
    type: str  # access/refresh
    created_at: datetime = datetime.utcnow()
    expires_at: datetime
    is_active: bool = True

    class Settings:
        collection = "tokens"
        indexes = [
            IndexModel([("token", 1)], unique=True),
            IndexModel([("user_id", 1)]),
            IndexModel([("expires_at", 1)]),
            IndexModel([("is_active", 1)]),
        ]


class Permission(Document):
    code: Indexed(str, unique=True)
    module: str
    description: str
    is_active: bool = True

    class Settings:
        collection = "permissions"


class Role(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    permissions: List[str] = []  # Permission IDs
    is_active: bool = True
    created_at: datetime = datetime.utcnow()

    class Settings:
        collection = "roles"
        indexes = [
            IndexModel([("name", 1)], unique=True),
            IndexModel([("is_active", 1)]),
        ]