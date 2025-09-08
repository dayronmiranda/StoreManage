from beanie import Document, Indexed
from datetime import datetime
from typing import Optional
from pydantic import Field
from pymongo import IndexModel


class Warehouse(Document):
    code: Indexed(str, unique=True)
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    type: str  # warehouse/store
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Additional information
    manager: Optional[str] = None
    max_capacity: Optional[int] = None

    class Settings:
        collection = "warehouses"
        indexes = [
            IndexModel([("code", 1)], unique=True),
            IndexModel([("name", 1)]),
            IndexModel([("type", 1)]),
            IndexModel([("is_active", 1)]),
        ]