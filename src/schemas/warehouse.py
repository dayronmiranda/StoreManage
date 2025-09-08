from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = None
    type: str = Field(..., pattern="^(warehouse|store)$")
    is_active: bool = True
    manager: Optional[str] = None
    max_capacity: Optional[int] = Field(None, gt=0)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = Field(None, pattern="^(warehouse|store)$")
    is_active: Optional[bool] = None
    manager: Optional[str] = None
    max_capacity: Optional[int] = Field(None, gt=0)


class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class WarehouseListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    type: str
    is_active: bool