from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, List
from pydantic import Field, BaseModel
from decimal import Decimal
from pymongo import IndexModel


class TransferDetail(BaseModel):  # Embedded
    product_id: str
    product_code: str  # Denormalized
    product_name: str  # Denormalized
    requested_quantity: Decimal
    sent_quantity: Optional[Decimal] = None
    received_quantity: Optional[Decimal] = None
    transit_quantity: Decimal = Decimal("0")
    discrepancy: Optional[Decimal] = None
    discrepancy_note: Optional[str] = None


class Transfer(Document):
    transfer_number: Indexed(str, unique=True)
    source_warehouse_id: str
    destination_warehouse_id: str
    requested_by_user_id: str
    approved_by_user_id: Optional[str] = None
    dispatched_by_user_id: Optional[str] = None
    received_by_user_id: Optional[str] = None
    status: str = "pending"  # pending/approved/rejected/in_transit/completed/cancelled
    details: List[TransferDetail]  # Embedded
    request_date: datetime = Field(default_factory=datetime.utcnow)
    approval_date: Optional[datetime] = None
    departure_date: Optional[datetime] = None
    estimated_arrival_date: Optional[datetime] = None
    actual_arrival_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    reason: str
    notes: Optional[str] = None
    
    # Additional information
    transport_cost: Optional[Decimal] = None
    priority: str = "normal"  # low/normal/high/urgent
    
    class Settings:
        collection = "transfers"
        indexes = [
            IndexModel([("transferNumber", 1)], unique=True),
            IndexModel([("sourceWarehouseId", 1)]),
            IndexModel([("destinationWarehouseId", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("requestDate", -1)]),
            IndexModel([("requestedByUserId", 1)]),
        ]


class GoodsInTransit(Document):
    transfer_id: str
    current_location: Optional[str] = None
    transit_status: str  # preparing/in_route/at_destination/delivered
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str
    notes: Optional[str] = None
    
    # Tracking information
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature: Optional[float] = None
    
    class Settings:
        collection = "merchandise_transit"
        indexes = [
            IndexModel([("transferId", 1)]),
            IndexModel([("transitStatus", 1)]),
            IndexModel([("updatedAt", -1)]),
        ]