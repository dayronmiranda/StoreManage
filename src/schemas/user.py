from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass


# Schemas base
@dataclass
class UserBase:
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    is_active: bool = True
    roles: List[str] = None
    allowed_warehouses: List[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.allowed_warehouses is None:
            self.allowed_warehouses = []


@dataclass
class UserCreate(UserBase):
    pass


@dataclass
class UserUpdate:
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    allowed_warehouses: Optional[List[str]] = None


@dataclass
class UserResponse:
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    created_at: datetime
    is_active: bool = True
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    roles: List[str] = None
    allowed_warehouses: List[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.allowed_warehouses is None:
            self.allowed_warehouses = []


@dataclass
class UserLogin:
    username: str
    password: str


# Token classes removed for MVP simplification


# Schemas para Rol
@dataclass
class RoleBase:
    name: str
    description: Optional[str] = None
    permissions: List[str] = None
    is_active: bool = True

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


@dataclass
class RoleCreate(RoleBase):
    pass


@dataclass
class RoleUpdate:
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


@dataclass
class RoleResponse(RoleBase):
    id: str
    created_at: datetime


# Schemas para Permiso
@dataclass
class PermissionBase:
    code: str
    module: str
    description: str
    is_active: bool = True


@dataclass
class PermissionCreate(PermissionBase):
    pass


@dataclass
class PermissionResponse(PermissionBase):
    id: str
