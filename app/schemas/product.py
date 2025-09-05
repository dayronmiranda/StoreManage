from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Schemas for Category
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[str] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime


# Schemas for UnitOfMeasure
class UnitOfMeasureBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    is_active: bool = True


class UnitOfMeasureCreate(UnitOfMeasureBase):
    pass


class UnitOfMeasureUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    abbreviation: Optional[str] = Field(None, min_length=1, max_length=10)
    is_active: Optional[bool] = None


class UnitOfMeasureResponse(UnitOfMeasureBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str


# Schemas for PriceHistory
class PriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    previous_price: Decimal
    new_price: Decimal
    user_id: str
    change_date: datetime
    reason: Optional[str] = None


# Schemas for Product
class ProductBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: str
    unit_of_measure_id: str
    current_price: Decimal = Field(..., gt=0)
    cost: Decimal = Field(..., ge=0)
    is_active: bool = True
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: Optional[str] = None
    unit_of_measure_id: Optional[str] = None
    current_price: Optional[Decimal] = Field(None, gt=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: datetime
    image_path: Optional[str] = None
    price_history: List[PriceHistoryResponse] = []
    
    # Related fields (optional)
    category: Optional[CategoryResponse] = None
    unitOfMeasure: Optional[UnitOfMeasureResponse] = None


class ProductListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    code: str
    name: str
    current_price: Decimal
    is_active: bool
    category: Optional[str] = None  # Name only
    unit_of_measure: Optional[str] = None  # Abbreviation only


# Schema for price change
class PriceChange(BaseModel):
    new_price: Decimal = Field(..., gt=0)
    reason: Optional[str] = None