from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, List, Any
from pydantic import Field, BaseModel, field_validator
from decimal import Decimal
from pymongo import IndexModel, TEXT
from bson import Decimal128


class Category(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    parent_category_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        collection = "categories"
        indexes = [
            IndexModel([("name", 1)], unique=True),
            IndexModel([("is_active", 1)]),
            IndexModel([("parent_category_id", 1)]),
        ]


class UnitOfMeasure(Document):
    name: Indexed(str, unique=True)  # kilogram, unit, liter, etc.
    abbreviation: Indexed(str, unique=True)  # kg, unit, lt
    is_active: bool = True
    
    class Settings:
        collection = "units_of_measure"
        indexes = [
            IndexModel([("name", 1)], unique=True),
            IndexModel([("abbreviation", 1)], unique=True),
        ]


class PriceHistory(BaseModel):
    previous_price: Decimal
    new_price: Decimal
    user_id: str
    change_date: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    
    @field_validator('previous_price', 'new_price', mode='before')
    @classmethod
    def convert_decimal128(cls, v: Any) -> Any:
        if isinstance(v, Decimal128):
            return Decimal(str(v))
        return v


class Product(Document):
    code: Indexed(str, unique=True)
    name: Indexed(str)
    description: Optional[str] = None
    category_id: str
    unit_of_measure_id: str
    current_price: Decimal
    cost: Decimal
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    price_history: List[PriceHistory] = []  # Embedded
    image_path: Optional[str] = None
    
    # Additional fields for control
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    
    @field_validator('current_price', 'cost', 'min_stock', 'max_stock', mode='before')
    @classmethod
    def convert_decimal128(cls, v: Any) -> Any:
        if isinstance(v, Decimal128):
            return Decimal(str(v))
        return v
    
    class Settings:
        collection = "products"
        indexes = [
            IndexModel([("code", 1)], unique=True),
            IndexModel([("name", TEXT)]),  # For text search
            IndexModel([("category_id", 1)]),
            IndexModel([("is_active", 1)]),
            IndexModel([("created_at", -1)]),
        ]