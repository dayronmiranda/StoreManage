from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from datetime import datetime

from app.models.transfers import Transfer, GoodsInTransit
from app.models.warehouses import Warehouse
from app.models.user import User
from app.schemas.transfer import (
    TransferCreate,
    TransferUpdate,
    TransferResponse,
    TransferListResponse,
    ApproveTransfer,
    DispatchTransfer,
    ReceiveTransfer,
    MerchandiseTransitCreate,
    MerchandiseTransitResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.get("", response_model=PaginatedResponse[TransferListResponse])
async def list_transfers(
    pagination: PaginationParams = Depends(),
    origin_warehouse_id: Optional[str] = Query(None, description="Filter by origin warehouse"),
    destination_warehouse_id: Optional[str] = Query(None, description="Filter by destination warehouse"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    requesting_user_id: Optional[str] = Query(None, description="Filter by requesting user"),
    current_user: User = Depends(get_current_active_user)
):
    """List transfers with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if origin_warehouse_id:
        query_params["origin_warehouse_id"] = origin_warehouse_id
    
    if destination_warehouse_id:
        query_params["destination_warehouse_id"] = destination_warehouse_id
    
    if status:
        query_params["status"] = status
    
    if priority:
        query_params["priority"] = priority
    
    if requesting_user_id:
        query_params["requesting_user_id"] = requesting_user_id
    
    # Aggregation pipeline to get related information
    pipeline = [
        {"$match": query_params},
        {"$sort": {"request_date": -1}},
        {
            "$lookup": {
                "from": "warehouses",
                "localField": "origin_warehouse_id",
                "foreignField": "_id",
                "as": "origin_warehouse"
            }
        },
        {
            "$lookup": {
                "from": "warehouses",
                "localField": "destination_warehouse_id",
                "foreignField": "_id",
                "as": "destination_warehouse"
            }
        }
    ]
    
    # Get total
    total_pipeline = pipeline + [{"$count": "total"}]
    total_result = await Transfer.aggregate(total_pipeline).to_list()
    total_transfers = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    transfers = await Transfer.aggregate(pipeline).to_list()
    
    # Convert to response
    transfer_responses = []
    for transfer in transfers:
        origin_warehouse = transfer.get("origin_warehouse", [{}])[0] if transfer.get("origin_warehouse") else {}
        destination_warehouse = transfer.get("destination_warehouse", [{}])[0] if transfer.get("destination_warehouse") else {}
        
        transfer_responses.append(TransferListResponse(
            id=str(transfer["_id"]),
            transfer_number=transfer["transfer_number"],
            request_date=transfer["request_date"],
            origin_warehouse_name=origin_warehouse.get("name"),
            destination_warehouse_name=destination_warehouse.get("name"),
            status=transfer["status"],
            priority=transfer["priority"]
        ))
    
    total_pages = (total_transfers + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=transfer_responses,
        total=total_transfers,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    transfer_data: TransferCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new transfer"""
    
    try:
        # Create transfer using the service
        transfer = await TransferService.create_transfer(
            transfer_data, str(current_user.id)
        )
        
        # Get related information for the response
        origin_warehouse = await Warehouse.get(transfer.origin_warehouse_id)
        destination_warehouse = await Warehouse.get(transfer.destination_warehouse_id)
        
        return TransferResponse(
            id=str(transfer.id),
            transfer_number=transfer.transfer_number,
            origin_warehouse_id=transfer.origin_warehouse_id,
            destination_warehouse_id=transfer.destination_warehouse_id,
            requesting_user_id=transfer.requesting_user_id,
            approving_user_id=transfer.approving_user_id,
            dispatching_user_id=transfer.dispatching_user_id,
            receiving_user_id=transfer.receiving_user_id,
            status=transfer.status,
            details=transfer.details,
            request_date=transfer.request_date,
            approval_date=transfer.approval_date,
            dispatch_date=transfer.dispatch_date,
            estimated_arrival_date=transfer.estimated_arrival_date,
            actual_arrival_date=transfer.actual_arrival_date,
            completion_date=transfer.completion_date,
            carrier=transfer.carrier,
            tracking_number=transfer.tracking_number,
            reason=transfer.reason,
            observations=transfer.observations,
            transport_cost=transfer.transport_cost,
            priority=transfer.priority,
            origin_warehouse_name=origin_warehouse.name if origin_warehouse else None,
            destination_warehouse_name=destination_warehouse.name if destination_warehouse else None,
            requesting_user_name=f"{current_user.first_name} {current_user.last_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transfer: {str(e)}"
        )


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get transfer by ID"""
    
    try:
        transfer = await Transfer.get(PydanticObjectId(transfer_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    # Get related information
    origin_warehouse = await Warehouse.get(transfer.origin_warehouse_id)
    destination_warehouse = await Warehouse.get(transfer.destination_warehouse_id)
    requesting_user = await User.get(transfer.requesting_user_id)
    
    return TransferResponse(
        id=str(transfer.id),
        transfer_number=transfer.transfer_number,
        origin_warehouse_id=transfer.origin_warehouse_id,
        destination_warehouse_id=transfer.destination_warehouse_id,
        requesting_user_id=transfer.requesting_user_id,
        approving_user_id=transfer.approving_user_id,
        dispatching_user_id=transfer.dispatching_user_id,
        receiving_user_id=transfer.receiving_user_id,
        status=transfer.status,
        details=transfer.details,
        request_date=transfer.request_date,
        approval_date=transfer.approval_date,
        dispatch_date=transfer.dispatch_date,
        estimated_arrival_date=transfer.estimated_arrival_date,
        actual_arrival_date=transfer.actual_arrival_date,
        completion_date=transfer.completion_date,
        carrier=transfer.carrier,
        tracking_number=transfer.tracking_number,
        reason=transfer.reason,
        observations=transfer.observations,
        transport_cost=transfer.transport_cost,
        priority=transfer.priority,
        origin_warehouse_name=origin_warehouse.name if origin_warehouse else None,
        destination_warehouse_name=destination_warehouse.name if destination_warehouse else None,
        requesting_user_name=f"{requesting_user.first_name} {requesting_user.last_name}" if requesting_user else None
    )


@router.patch("/{transfer_id}/approve")
async def approve_transfer(
    transfer_id: str,
    approval_data: ApproveTransfer,
    current_user: User = Depends(get_current_active_user)
):
    """Approve transfer"""
    
    try:
        transfer = await TransferService.approve_transfer(
            transfer_id, str(current_user.id), approval_data
        )
        return {
            "message": "Transfer approved successfully",
            "transfer_number": transfer.transfer_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving transfer: {str(e)}"
        )


@router.patch("/{transfer_id}/reject")
async def reject_transfer(
    transfer_id: str,
    reason: str,
    current_user: User = Depends(get_current_active_user)
):
    """Reject transfer"""
    
    try:
        transfer = await TransferService.reject_transfer(
            transfer_id, str(current_user.id), reason
        )
        return {
            "message": "Transfer rejected successfully",
            "transfer_number": transfer.transfer_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting transfer: {str(e)}"
        )


@router.patch("/{transfer_id}/dispatch")
async def dispatch_transfer(
    transfer_id: str,
    dispatch_data: DispatchTransfer,
    current_user: User = Depends(get_current_active_user)
):
    """Dispatch transfer (outbound from origin warehouse)"""
    
    try:
        transfer = await TransferService.dispatch_transfer(
            transfer_id, str(current_user.id), dispatch_data
        )
        return {
            "message": "Transfer dispatched successfully",
            "transfer_number": transfer.transfer_number,
            "tracking_number": transfer.tracking_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error dispatching transfer: {str(e)}"
        )


@router.patch("/{transfer_id}/receive")
async def receive_transfer(
    transfer_id: str,
    reception_data: ReceiveTransfer,
    current_user: User = Depends(get_current_active_user)
):
    """Receive transfer (inbound to destination warehouse)"""
    
    try:
        transfer = await TransferService.receive_transfer(
            transfer_id, str(current_user.id), reception_data
        )
        return {
            "message": "Transfer received successfully",
            "transfer_number": transfer.transfer_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error receiving transfer: {str(e)}"
        )


@router.patch("/{transfer_id}/cancel")
async def cancel_transfer(
    transfer_id: str,
    reason: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel transfer"""
    
    try:
        transfer = await TransferService.cancel_transfer(
            transfer_id, str(current_user.id), reason
        )
        return {
            "message": "Transfer canceled successfully",
            "transfer_number": transfer.transfer_number
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling transfer: {str(e)}"
        )


@router.put("/{transfer_id}", response_model=TransferResponse)
async def update_transfer(
    transfer_id: str,
    transfer_data: TransferUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update transfer (only if pending)"""
    
    try:
        transfer = await Transfer.get(PydanticObjectId(transfer_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    if transfer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending transfers can be updated"
        )
    
    # Update fields
    update_data = transfer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transfer, field, value)
    
    await transfer.save()
    
    # Get related information
    origin_warehouse = await Warehouse.get(transfer.origin_warehouse_id)
    destination_warehouse = await Warehouse.get(transfer.destination_warehouse_id)
    requesting_user = await User.get(transfer.requesting_user_id)
    
    return TransferResponse(
        id=str(transfer.id),
        transfer_number=transfer.transfer_number,
        origin_warehouse_id=transfer.origin_warehouse_id,
        destination_warehouse_id=transfer.destination_warehouse_id,
        requesting_user_id=transfer.requesting_user_id,
        approving_user_id=transfer.approving_user_id,
        dispatching_user_id=transfer.dispatching_user_id,
        receiving_user_id=transfer.receiving_user_id,
        status=transfer.status,
        details=transfer.details,
        request_date=transfer.request_date,
        approval_date=transfer.approval_date,
        dispatch_date=transfer.dispatch_date,
        estimated_arrival_date=transfer.estimated_arrival_date,
        actual_arrival_date=transfer.actual_arrival_date,
        completion_date=transfer.completion_date,
        carrier=transfer.carrier,
        tracking_number=transfer.tracking_number,
        reason=transfer.reason,
        observations=transfer.observations,
        transport_cost=transfer.transport_cost,
        priority=transfer.priority,
        origin_warehouse_name=origin_warehouse.name if origin_warehouse else None,
        destination_warehouse_name=destination_warehouse.name if destination_warehouse else None,
        requesting_user_name=f"{requesting_user.first_name} {requesting_user.last_name}" if requesting_user else None
    )


# TRANSIT ENDPOINTS
@router.get("/{transfer_id}/transit", response_model=List[MerchandiseTransitResponse])
async def get_transfer_transit_history(
    transfer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get transit history of a transfer"""
    
    # Verify that transfer exists
    try:
        transfer = await Transfer.get(PydanticObjectId(transfer_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    # Get transit records
    transits = await GoodsInTransit.find(
        {"transfer_id": transfer_id}
    ).sort([("update_date", -1)]).to_list()
    
    return [
        MerchandiseTransitResponse(
            id=str(transit.id),
            transfer_id=transit.transfer_id,
            current_location=transit.current_location,
            transit_status=transit.transit_status,
            update_date=transit.update_date,
            updated_by=transit.updated_by,
            notes=transit.notes,
            latitude=transit.latitude,
            longitude=transit.longitude,
            temperature=transit.temperature
        )
        for transit in transits
    ]


@router.post("/{transfer_id}/transit", response_model=MerchandiseTransitResponse)
async def update_transfer_transit(
    transfer_id: str,
    transit_data: MerchandiseTransitCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Update transit status of a transfer"""
    
    # Verify that transfer exists and is in transit
    try:
        transfer = await Transfer.get(PydanticObjectId(transfer_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    if transfer.status != "in_transit":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only in-transit transfers can be updated"
        )
    
    # Create transit record
    transit = GoodsInTransit(
        transfer_id=transfer_id,
        current_location=transit_data.current_location,
        transit_status=transit_data.transit_status,
        updated_by=str(current_user.id),
        notes=transit_data.notes,
        latitude=transit_data.latitude,
        longitude=transit_data.longitude,
        temperature=transit_data.temperature
    )
    
    await transit.insert()
    
    return MerchandiseTransitResponse(
        id=str(transit.id),
        transfer_id=transit.transfer_id,
        current_location=transit.current_location,
        transit_status=transit.transit_status,
        update_date=transit.update_date,
        updated_by=transit.updated_by,
        notes=transit.notes,
        latitude=transit.latitude,
        longitude=transit.longitude,
        temperature=transit.temperature
    )
