from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId

from app.models.warehouses import Warehouse
from app.models.user import User
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
    WarehouseListResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.get("", response_model=PaginatedResponse[WarehouseListResponse])
async def list_warehouses(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name or code"),
    type: Optional[str] = Query(None, description="Filter by type (warehouse/store)"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List warehouses with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if search:
        query_params["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    if type:
        query_params["type"] = type
    
    if active is not None:
        query_params["is_active"] = active
    
    # Get total
    total_warehouses = await Warehouse.find(query_params).count()
    
    # Get paginated warehouses
    skip = (pagination.page - 1) * pagination.size
    warehouse_list = await Warehouse.find(query_params).skip(skip).limit(pagination.size).to_list()
    
    # Convert to response
    warehouse_responses = [
        WarehouseListResponse(
            id=str(warehouse.id),
            code=warehouse.code,
            name=warehouse.name,
            type=warehouse.type,
            is_active=warehouse.is_active
        )
        for warehouse in warehouse_list
    ]
    
    total_pages = (total_warehouses + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=warehouse_responses,
        total=total_warehouses,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new warehouse"""
    
    # Verify that code does not exist
    existing_warehouse = await Warehouse.find_one({"code": warehouse_data.code})
    if existing_warehouse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Warehouse code already exists"
        )
    
    # Create warehouse
    warehouse = Warehouse(
        code=warehouse_data.code.upper(),
        name=warehouse_data.name,
        address=warehouse_data.address,
        phone=warehouse_data.phone,
        type=warehouse_data.type,
        is_active=warehouse_data.is_active,
        manager=warehouse_data.manager,
        max_capacity=warehouse_data.max_capacity
    )
    
    await warehouse.insert()
    
    return WarehouseResponse(
        id=str(warehouse.id),
        code=warehouse.code,
        name=warehouse.name,
        address=warehouse.address,
        phone=warehouse.phone,
        type=warehouse.type,
        is_active=warehouse.is_active,
        manager=warehouse.manager,
        max_capacity=warehouse.max_capacity,
        created_at=warehouse.created_at
    )


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get warehouse by ID"""
    
    try:
        warehouse = await Warehouse.get(PydanticObjectId(warehouse_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    return WarehouseResponse(
        id=str(warehouse.id),
        code=warehouse.code,
        name=warehouse.name,
        address=warehouse.address,
        phone=warehouse.phone,
        type=warehouse.type,
        is_active=warehouse.is_active,
        manager=warehouse.manager,
        max_capacity=warehouse.max_capacity,
        created_at=warehouse.created_at
    )


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    warehouse_data: WarehouseUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update warehouse"""
    
    try:
        warehouse = await Warehouse.get(PydanticObjectId(warehouse_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    # Verify that code does not exist in another warehouse
    if warehouse_data.code and warehouse_data.code != warehouse.code:
        existing_warehouse = await Warehouse.find_one({"code": warehouse_data.code})
        if existing_warehouse:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse code already exists"
            )
    
    # Update fields
    update_data = warehouse_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "code" and value:
            setattr(warehouse, field, value.upper())
        else:
            setattr(warehouse, field, value)
    
    await warehouse.save()
    
    return WarehouseResponse(
        id=str(warehouse.id),
        code=warehouse.code,
        name=warehouse.name,
        address=warehouse.address,
        phone=warehouse.phone,
        type=warehouse.type,
        is_active=warehouse.is_active,
        manager=warehouse.manager,
        max_capacity=warehouse.max_capacity,
        created_at=warehouse.created_at
    )


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete warehouse (deactivate)"""
    
    try:
        warehouse = await Warehouse.get(PydanticObjectId(warehouse_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    # Deactivate warehouse instead of deleting
    warehouse.is_active = False
    await warehouse.save()
    
    return {"message": "Warehouse deleted successfully"}


@router.post("/{warehouse_id}/toggle-status")
async def toggle_warehouse_status(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Activate/deactivate warehouse"""
    
    try:
        warehouse = await Warehouse.get(PydanticObjectId(warehouse_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    # Change status
    warehouse.is_active = not warehouse.is_active
    await warehouse.save()
    
    status_str = "activated" if warehouse.is_active else "deactivated"
    return {"message": f"Warehouse {status_str} successfully"}
