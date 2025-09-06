from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


# Inventory Schemas
class InventoryBase(BaseModel):
    warehouse_id: str
    product_id: str
    available_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    reserved_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    outbound_transit_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    inbound_transit_quantity: Decimal = Field(default=Decimal("0"), ge=0)


class InventoryResponse(InventoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    last_updated_date: datetime
    total_quantity: Decimal
    
    # Related information (optional)
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    warehouse_name: Optional[str] = None


class InventoryListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    warehouse_id: str
    product_id: str
    available_quantity: Decimal
    total_quantity: Decimal
    product_name: Optional[str] = None
    product_code: Optional[str] = None


# Inventory Movement Schemas
class InventoryMovementBase(BaseModel):
    warehouse_id: str
    product_id: str
    movement_type: str = Field(..., pattern="^(inbound|outbound|adjustment|transfer_outbound|transfer_inbound)$")
    quantity: Decimal = Field(..., ge=0)  # Changed from gt=0 to ge=0 to allow zero for adjustments
    reason: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    unit_cost: Optional[Decimal] = Field(None, ge=0)


class InventoryMovementCreate(InventoryMovementBase):
    pass


class InventoryMovementResponse(InventoryMovementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    previous_quantity: Decimal
    new_quantity: Decimal
    user_id: str
    movement_date: datetime
    total_value: Optional[Decimal] = None
    
    # Related information (optional)
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    warehouse_name: Optional[str] = None
    user_name: Optional[str] = None


# Inventory Adjustment Schema
class InventoryAdjustment(BaseModel):
    warehouse_id: str
    product_id: str
    new_quantity: Decimal = Field(..., ge=0)
    reason: str = Field(..., min_length=5, max_length=500)


# Inventory Query Schema
class InventoryQuery(BaseModel):
    warehouse_id: Optional[str] = None
    product_id: Optional[str] = None
    only_with_stock: bool = False
    minimum_stock: bool = False