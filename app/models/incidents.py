from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, List
from pydantic import Field, BaseModel
from decimal import Decimal
from pymongo import IndexModel


class IncidentType(Document):
    code: Indexed(str, unique=True)
    name: str
    category: str  # reception/operation/inventory/sale
    isActive: bool = True
    description: Optional[str] = None
    
    class Settings:
        collection = "incident_types"
        indexes = [
            IndexModel([("code", 1)], unique=True),
            IndexModel([("category", 1)]),
            IndexModel([("isActive", 1)]),
        ]


class IncidentDetail(BaseModel):  # Embedded
    productId: str
    productCode: str  # Denormalized
    productName: str  # Denormalized
    affectedQuantity: Decimal
    unitCost: Decimal
    totalCost: Decimal


class IncidentEvidence(BaseModel):  # Embedded
    filePath: str
    fileType: str  # image/document
    description: Optional[str] = None
    uploadDate: datetime = Field(default_factory=datetime.utcnow)
    fileSize: Optional[int] = None


class Incident(Document):
    incidentNumber: Indexed(str, unique=True)
    incidentTypeId: str
    warehouseId: str
    detectionMoment: str  # reception/operation/inventory/sale
    reportedByUserId: str
    status: str = "open"  # open/investigating/resolved/closed
    description: str
    actionsTaken: Optional[str] = None
    economicImpact: Decimal = Decimal("0")
    incidentDate: datetime = Field(default_factory=datetime.utcnow)
    resolutionDate: Optional[datetime] = None
    referenceId: Optional[str] = None  # Sale ID, transfer ID, etc.
    referenceType: Optional[str] = None  # sale/transfer/reception
    details: List[IncidentDetail] = []  # Embedded
    evidence: List[IncidentEvidence] = []  # Embedded
    
    # Additional information
    priority: str = "medium"  # low/medium/high/critical
    resolutionResponsibleId: Optional[str] = None
    
    class Settings:
        collection = "incidents"
        indexes = [
            IndexModel([("incidentNumber", 1)], unique=True),
            IndexModel([("incidentTypeId", 1)]),
            IndexModel([("warehouseId", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("incidentDate", -1)]),
            IndexModel([("reportedByUserId", 1)]),
            IndexModel([("priority", 1)]),
        ]