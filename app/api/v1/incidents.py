from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from datetime import datetime

from app.models.incidents import Incident, IncidentType
from app.models.warehouses import Warehouse
from app.models.user import User
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentListResponse,
    ResolveIncident,
    IncidentTypeCreate,
    IncidentTypeResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.utils.generators import generate_incident_number

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=PaginatedResponse[IncidentListResponse])
async def list_incidents(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    incident_type_id: Optional[str] = Query(None, description="Filter by incident type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    reported_by_user_id: Optional[str] = Query(None, description="Filter by reporting user"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_active_user)
):
    """List incidents with pagination and filters"""
    
    # Build query
    query = {}
    
    if warehouse_id:
        query["warehouseId"] = warehouse_id
    
    if incident_type_id:
        query["incidentTypeId"] = incident_type_id
    
    if status:
        query["status"] = status
    
    if priority:
        query["priority"] = priority
    
    if reported_by_user_id:
        query["reportedByUserId"] = reported_by_user_id
    
    # Date filter
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["incidentDate"] = date_query
    
    # Aggregation pipeline to get related information
    pipeline = [
        {"$match": query},
        {"$sort": {"incidentDate": -1}},
        {
            "$lookup": {
                "from": "incident_types",
                "localField": "incidentTypeId",
                "foreignField": "_id",
                "as": "incidentType"
            }
        },
        {
            "$lookup": {
                "from": "warehouses",
                "localField": "warehouseId",
                "foreignField": "_id",
                "as": "warehouse"
            }
        }
    ]
    
    # Get total
    total_pipeline = pipeline + [{"$count": "total"}]
    total_result = await Incident.aggregate(total_pipeline).to_list()
    total = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    incidents = await Incident.aggregate(pipeline).to_list()
    
    # Convert to response
    incidents_response = []
    for incident in incidents:
        incident_type = incident.get("incidentType", [{}])[0] if incident.get("incidentType") else {}
        warehouse = incident.get("warehouse", [{}])[0] if incident.get("warehouse") else {}
        
        incidents_response.append(IncidentListResponse(
            id=str(incident["_id"]),
            incident_number=incident["incidentNumber"],
            incident_date=incident["incidentDate"],
            incident_type_name=incident_type.get("name"),
            warehouse_name=warehouse.get("name"),
            status=incident["status"],
            priority=incident["priority"],
            economic_impact=incident["economicImpact"]
        ))
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=incidents_response,
        total=total,
        page=pagination.page,
        pages=pages,
        size=pagination.size,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new incident"""
    
    # Validate incident type
    incident_type = await IncidentType.get(incident_data.incident_type_id)
    if not incident_type or not incident_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident type not found or inactive"
        )
    
    # Validate warehouse
    warehouse = await Warehouse.get(incident_data.warehouse_id)
    if not warehouse or not warehouse.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found or inactive"
        )
    
    # Calculate initial economic impact
    economic_impact = sum(
        detail.affected_quantity * detail.unit_cost 
        for detail in incident_data.details
    )
    
    # Create incident
    incident = Incident(
        incident_number=await generate_incident_number(),
        incident_type_id=incident_data.incident_type_id,
        warehouse_id=incident_data.warehouse_id,
        detection_time=incident_data.detection_time,
        reported_by_user_id=str(current_user.id),
        status="open",
        description=incident_data.description,
        economic_impact=economic_impact,
        reference_id=incident_data.reference_id,
        reference_type=incident_data.reference_type,
        details=incident_data.details,
        priority=incident_data.priority
    )
    
    await incident.insert()
    
    return IncidentResponse(
        id=str(incident.id),
        incident_number=incident.incident_number,
        incident_type_id=incident.incident_type_id,
        warehouse_id=incident.warehouse_id,
        detection_time=incident.detection_time,
        reported_by_user_id=incident.reported_by_user_id,
        status=incident.status,
        description=incident.description,
        actions_taken=incident.actions_taken,
        economic_impact=incident.economic_impact,
        incident_date=incident.incident_date,
        resolution_date=incident.resolution_date,
        reference_id=incident.reference_id,
        reference_type=incident.reference_type,
        details=incident.details,
        evidence=incident.evidence,
        priority=incident.priority,
        resolution_responsible_id=incident.resolution_responsible_id,
        incident_type_name=incident_type.name,
        warehouse_name=warehouse.name,
        reported_by_user_name=f"{current_user.first_name} {current_user.last_name}"
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get incident by ID"""
    
    try:
        incident = await Incident.get(PydanticObjectId(incident_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Get related information
    incident_type = await IncidentType.get(incident.incident_type_id)
    warehouse = await Warehouse.get(incident.warehouse_id)
    reported_by_user = await User.get(incident.reported_by_user_id)
    
    return IncidentResponse(
        id=str(incident.id),
        incident_number=incident.incident_number,
        incident_type_id=incident.incident_type_id,
        warehouse_id=incident.warehouse_id,
        detection_time=incident.detection_time,
        reported_by_user_id=incident.reported_by_user_id,
        status=incident.status,
        description=incident.description,
        actions_taken=incident.actions_taken,
        economic_impact=incident.economic_impact,
        incident_date=incident.incident_date,
        resolution_date=incident.resolution_date,
        reference_id=incident.reference_id,
        reference_type=incident.reference_type,
        details=incident.details,
        evidence=incident.evidence,
        priority=incident.priority,
        resolution_responsible_id=incident.resolution_responsible_id,
        incident_type_name=incident_type.name if incident_type else None,
        warehouse_name=warehouse.name if warehouse else None,
        reported_by_user_name=f"{reported_by_user.first_name} {reported_by_user.last_name}" if reported_by_user else None
    )


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    incident_data: IncidentUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update incident"""
    
    try:
        incident = await Incident.get(PydanticObjectId(incident_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if incident.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a resolved incident"
        )
    
    # Update fields
    update_data = incident_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)
    
    await incident.save()
    
    # Get related information
    incident_type = await IncidentType.get(incident.incident_type_id)
    warehouse = await Warehouse.get(incident.warehouse_id)
    reported_by_user = await User.get(incident.reported_by_user_id)
    
    return IncidentResponse(
        id=str(incident.id),
        incident_number=incident.incident_number,
        incident_type_id=incident.incident_type_id,
        warehouse_id=incident.warehouse_id,
        detection_time=incident.detection_time,
        reported_by_user_id=incident.reported_by_user_id,
        status=incident.status,
        description=incident.description,
        actions_taken=incident.actions_taken,
        economic_impact=incident.economic_impact,
        incident_date=incident.incident_date,
        resolution_date=incident.resolution_date,
        reference_id=incident.reference_id,
        reference_type=incident.reference_type,
        details=incident.details,
        evidence=incident.evidence,
        priority=incident.priority,
        resolution_responsible_id=incident.resolution_responsible_id,
        incident_type_name=incident_type.name if incident_type else None,
        warehouse_name=warehouse.name if warehouse else None,
        reported_by_user_name=f"{reported_by_user.first_name} {reported_by_user.last_name}" if reported_by_user else None
    )


@router.patch("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    resolution_data: ResolveIncident,
    current_user: User = Depends(get_current_active_user)
):
    """Resolve incident"""
    
    try:
        incident = await Incident.get(PydanticObjectId(incident_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if incident.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident is already resolved"
        )
    
    # Update incident
    incident.status = "resolved"
    incident.actions_taken = resolution_data.actions_taken
    incident.economic_impact = resolution_data.economic_impact
    incident.resolution_date = datetime.utcnow()
    incident.resolution_responsible_id = str(current_user.id)
    
    await incident.save()
    
    return {
        "message": "Incident resolved successfully",
        "incident_number": incident.incident_number,
        "economic_impact": incident.economic_impact
    }


@router.patch("/{incident_id}/change-status")
async def change_incident_status(
    incident_id: str,
    new_status: str = Query(..., pattern="^(open|investigating|resolved|closed)$"),
    current_user: User = Depends(get_current_active_user)
):
    """Change incident status"""
    
    try:
        incident = await Incident.get(PydanticObjectId(incident_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Validate status transition
    valid_transitions = {
        "open": ["investigating", "resolved"],
        "investigating": ["open", "resolved"],
        "resolved": ["closed"],
        "closed": []
    }
    
    if new_status not in valid_transitions.get(incident.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change from {incident.status} to {new_status}"
        )
    
    # Update status
    incident.status = new_status
    if new_status == "resolved" and not incident.resolution_date:
        incident.resolution_date = datetime.utcnow()
        incident.resolution_responsible_id = str(current_user.id)
    
    await incident.save()
    
    return {
        "message": f"Status changed to {new_status} successfully",
        "incident_number": incident.incident_number
    }


# INCIDENT TYPES ENDPOINTS
@router.get("/types/", response_model=List[IncidentTypeResponse])
async def list_incident_types(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List incident types"""
    
    query = {}
    if category:
        query["category"] = category
    if is_active is not None:
        query["isActive"] = is_active
    
    types = await IncidentType.find(query).to_list()
    
    return [
        IncidentTypeResponse(
            id=str(type.id),
            code=type.code,
            name=type.name,
            category=type.category,
            is_active=type.is_active,
            description=type.description
        )
        for type in types
    ]


@router.post("/types/", response_model=IncidentTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_incident_type(
    type_data: IncidentTypeCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new incident type"""
    
    # Check if code already exists
    existing_type = await IncidentType.find_one({"code": type_data.code})
    if existing_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident type code already exists"
        )
    
    # Create incident type
    incident_type = IncidentType(
        code=type_data.code.upper(),
        name=type_data.name,
        category=type_data.category,
        is_active=type_data.is_active,
        description=type_data.description
    )
    
    await incident_type.insert()
    
    return IncidentTypeResponse(
        id=str(incident_type.id),
        code=incident_type.code,
        name=incident_type.name,
        category=incident_type.category,
        is_active=incident_type.is_active,
        description=incident_type.description
    )


@router.get("/statistics")
async def get_incident_statistics(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_active_user)
):
    """Get incident statistics"""
    
    # Build base query
    match_query = {}
    if warehouse_id:
        match_query["warehouseId"] = warehouse_id
    
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        match_query["incidentDate"] = date_query
    
    # Aggregation pipeline for statistics
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_incidents": {"$sum": 1},
                "open": {
                    "$sum": {"$cond": [{"$eq": ["$status", "open"]}, 1, 0]}
                },
                "investigating": {
                    "$sum": {"$cond": [{"$eq": ["$status", "investigating"]}, 1, 0]}
                },
                "resolved": {
                    "$sum": {"$cond": [{"$eq": ["$status", "resolved"]}, 1, 0]}
                },
                "closed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "closed"]}, 1, 0]}
                },
                "total_impact": {"$sum": "$economicImpact"},
                "average_impact": {"$avg": "$economicImpact"}
            }
        }
    ]
    
    result = await Incident.aggregate(pipeline).to_list()
    
    if not result:
        return {
            "total_incidents": 0,
            "open": 0,
            "investigating": 0,
            "resolved": 0,
            "closed": 0,
            "total_impact": 0,
            "average_impact": 0
        }
    
    return result[0]