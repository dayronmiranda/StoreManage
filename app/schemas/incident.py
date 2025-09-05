from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Schemas for IncidentType
class IncidentTypeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., pattern="^(reception|operation|inventory|sale)$")
    is_active: bool = True
    description: Optional[str] = None


class IncidentTypeCreate(IncidentTypeBase):
    pass


class IncidentTypeResponse(IncidentTypeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str


# Schemas for IncidentDetail
class IncidentDetailBase(BaseModel):
    product_id: str
    affected_quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(..., ge=0)


class IncidentDetailCreate(IncidentDetailBase):
    pass


class IncidentDetailResponse(IncidentDetailBase):
    model_config = ConfigDict(from_attributes=True)
    
    product_code: str
    product_name: str
    total_cost: Decimal


# Schemas for IncidentEvidence
class IncidentEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    file_path: str
    file_type: str
    description: Optional[str] = None
    upload_date: datetime
    file_size: Optional[int] = None


# Schemas for Incident
class IncidentBase(BaseModel):
    incident_type_id: str
    warehouse_id: str
    detection_moment: str = Field(..., pattern="^(reception|operation|inventory|sale)$")
    description: str = Field(..., min_length=10, max_length=1000)
    reference_id: Optional[str] = None
    reference_type: Optional[str] = Field(None, pattern="^(sale|transfer|reception)$")
    details: List[IncidentDetailCreate] = []
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    actions_taken: Optional[str] = None
    resolution_responsible_id: Optional[str] = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_number: str
    incident_type_id: str
    warehouse_id: str
    detection_moment: str
    reported_by_user_id: str
    status: str
    description: str
    actions_taken: Optional[str] = None
    economic_impact: Decimal
    incident_date: datetime
    resolution_date: Optional[datetime] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    details: List[IncidentDetailResponse] = []
    evidence: List[IncidentEvidenceResponse] = []
    priority: str
    resolution_responsible_id: Optional[str] = None
    
    # Related information (optional)
    incident_type_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    reported_by_user_name: Optional[str] = None


class IncidentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_number: str
    incident_date: datetime
    incident_type_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    status: str
    priority: str
    economic_impact: Decimal


# Schema for resolving incident
class ResolveIncident(BaseModel):
    actions_taken: str = Field(..., min_length=10, max_length=1000)
    economic_impact: Decimal = Field(default=Decimal("0"), ge=0)