from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, Any
from pydantic import Field, field_validator
from decimal import Decimal
from pymongo import IndexModel
from bson import Decimal128


class Inventory(Document):
    warehouse_id: str
    product_id: str
    available_quantity: Decimal = Decimal("0")
    reserved_quantity: Decimal = Decimal("0")
    outbound_transit_quantity: Decimal = Decimal("0")
    inbound_transit_quantity: Decimal = Decimal("0")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('available_quantity', 'reserved_quantity', 'outbound_transit_quantity', 'inbound_transit_quantity', mode='before')
    @classmethod
    def convert_decimal128(cls, v: Any) -> Any:
        if isinstance(v, Decimal128):
            return Decimal(str(v))
        return v
    
    # Calculated fields
    @property
    def total_quantity(self) -> Decimal:
        return (self.available_quantity + 
                self.reserved_quantity + 
                self.outbound_transit_quantity + 
                self.inbound_transit_quantity)
    
    class Settings:
        collection = "inventories"
        indexes = [
            IndexModel([("warehouse_id", 1), ("product_id", 1)], unique=True),
            IndexModel([("warehouse_id", 1)]),
            IndexModel([("product_id", 1)]),
            IndexModel([("updated_at", -1)]),
        ]


class InventoryMovement(Document):
    warehouse_id: str
    product_id: str
    movement_type: str  # inbound/outbound/adjustment/transfer_outbound/transfer_inbound
    quantity: Decimal
    previous_quantity: Decimal
    new_quantity: Decimal
    reference_id: Optional[str] = None  # Sale ID, transfer ID, etc.
    reference_type: Optional[str] = None  # sale/transfer/adjustment/incident
    reason: Optional[str] = None
    user_id: str
    movement_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional information
    unit_cost: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    
    @field_validator('quantity', 'previous_quantity', 'new_quantity', 'unit_cost', 'total_value', mode='before')
    @classmethod
    def convert_decimal128(cls, v: Any) -> Any:
        if isinstance(v, Decimal128):
            return Decimal(str(v))
        return v
    
    class Settings:
        collection = "inventory_movements"
        indexes = [
            IndexModel([("warehouse_id", 1)]),
            IndexModel([("product_id", 1)]),
            IndexModel([("movement_type", 1)]),
            IndexModel([("movement_date", -1)]),
            IndexModel([("reference_id", 1)]),
            IndexModel([("user_id", 1)]),
        ]