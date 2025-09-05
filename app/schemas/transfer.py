from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Schemas for TransferDetail
class TransferDetailBase(BaseModel):
    product_id: str
    requested_quantity: Decimal = Field(..., gt=0)


class TransferDetailCreate(TransferDetailBase):
    pass


class TransferDetailResponse(TransferDetailBase):
    model_config = ConfigDict(from_attributes=True)
    
    product_code: str
    product_name: str
    sent_quantity: Optional[Decimal] = None
    received_quantity: Optional[Decimal] = None
    quantity_in_transit: Decimal
    discrepancy: Optional[Decimal] = None
    discrepancy_observation: Optional[str] = None


# Schemas for Transfer
class TransferBase(BaseModel):
    source_warehouse_id: str
    destination_warehouse_id: str
    reason: str = Field(..., min_length=5, max_length=500)
    details: List[TransferDetailCreate] = Field(..., min_length=1)
    estimated_arrival_date: Optional[datetime] = None
    carrier: Optional[str] = None
    observations: Optional[str] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class TransferCreate(TransferBase):
    pass


class TransferUpdate(BaseModel):
    reason: Optional[str] = Field(None, min_length=5, max_length=500)
    estimated_arrival_date: Optional[datetime] = None
    carrier: Optional[str] = None
    observations: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|normal|high|urgent)$")


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    transfer_number: str
    source_warehouse_id: str
    destination_warehouse_id: str
    requesting_user_id: str
    approving_user_id: Optional[str] = None
    dispatching_user_id: Optional[str] = None
    receiving_user_id: Optional[str] = None
    status: str
    details: List[TransferDetailResponse]
    request_date: datetime
    approval_date: Optional[datetime] = None
    departure_date: Optional[datetime] = None
    estimated_arrival_date: Optional[datetime] = None
    actual_arrival_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    carrier: Optional[str] = None
    transport_guide: Optional[str] = None
    reason: str
    observations: Optional[str] = None
    transport_cost: Optional[Decimal] = None
    priority: str
    
    # Related information (optional)
    source_warehouse_name: Optional[str] = None
    destination_warehouse_name: Optional[str] = None
    requesting_user_name: Optional[str] = None


class TransferListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    transfer_number: str
    request_date: datetime
    source_warehouse_name: Optional[str] = None
    destination_warehouse_name: Optional[str] = None
    status: str
    priority: str


# Schemas for transfer actions
class ApproveTransfer(BaseModel):
    observations: Optional[str] = None


class DispatchTransfer(BaseModel):
    transport_guide: Optional[str] = None
    transport_cost: Optional[Decimal] = Field(None, ge=0)
    observations: Optional[str] = None


class ReceiveTransfer(BaseModel):
    received_details: List[dict]  # {product_id: str, received_quantity: Decimal, observation: str}
    observations: Optional[str] = None


# Schemas for MerchandiseTransit
class MerchandiseTransitBase(BaseModel):
    transfer_id: str
    current_location: Optional[str] = None
    transit_status: str = Field(..., pattern="^(in_preparation|in_route|at_destination|delivered)$")
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature: Optional[float] = None


class MerchandiseTransitCreate(MerchandiseTransitBase):
    pass


class MerchandiseTransitResponse(MerchandiseTransitBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    update_date: datetime
    updated_by: str