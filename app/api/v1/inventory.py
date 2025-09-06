from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from decimal import Decimal
from bson import Decimal128

from app.models.inventories import Inventory, InventoryMovement
from app.models.product import Product
from app.models.warehouses import Warehouse
from app.models.user import User
from app.schemas.inventory import (
    InventoryResponse,
    InventoryListResponse,
    InventoryMovementResponse,
    InventoryAdjustment,
    InventoryQuery
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.services.inventory_service import InventoryService


def convert_decimal128_to_decimal(value):
    """Convert Decimal128 to Decimal for Pydantic compatibility"""
    if isinstance(value, Decimal128):
        return Decimal(str(value))
    return value

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=PaginatedResponse[InventoryListResponse])
async def list_inventory(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    product_id: Optional[str] = Query(None, description="Filter by product"),
    only_with_stock: bool = Query(False, description="Only products with stock"),
    minimum_stock: bool = Query(False, description="Only products under minimum stock"),
    current_user: User = Depends(get_current_active_user)
):
    """List inventory with pagination and filters"""
    
    # Build base query
    query_params = {}
    
    # Convert string IDs to ObjectId for the query
    if warehouse_id:
        query_params["warehouseId"] = warehouse_id
    
    if product_id:
        query_params["productId"] = product_id
    
    if only_with_stock:
        query_params["availableQuantity"] = {"$gt": 0}

    # Get inventories using find instead of aggregate to simplify
    skip = (pagination.page - 1) * pagination.size
    
    # Count total
    total_inventory = await Inventory.find(query_params).count()
    
    # Get paginated inventories
    inventory_list = await Inventory.find(query_params).skip(skip).limit(pagination.size).to_list()
    
    # Convert to response getting related information
    inventory_responses = []
    for inv in inventory_list:
        # Get product and warehouse
        product = await Product.get(inv.productId)
        warehouse = await Warehouse.get(inv.warehouseId)
        
        # Apply minimum stock filter if necessary
        if minimum_stock and product and product.minimumStock:
            if inv.availableQuantity >= product.minimumStock:
                continue
        
        inventory_responses.append(InventoryListResponse(
            id=str(inv.id),
            warehouse_id=inv.warehouseId,
            product_id=inv.productId,
            available_quantity=inv.availableQuantity,
            total_quantity=inv.totalQuantity,
            product_name=product.name if product else None,
            product_code=product.code if product else None
        ))
    
    total_pages = (total_inventory + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=inventory_responses,
        total=total_inventory,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.get("/{warehouse_id}/{product_id}", response_model=InventoryResponse)
async def get_specific_inventory(
    warehouse_id: str,
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get specific inventory of a product in a warehouse"""
    
    # Verify that warehouse exists
    warehouse = await Warehouse.get(warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    # Verify that product exists
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get inventory
    inventory = await InventoryService.get_inventory(warehouse_id, product_id)
    
    if not inventory:
        # If it does not exist, create with quantity 0
        inventory = await InventoryService.create_or_update_inventory(
            warehouse_id, product_id, 0
        )
    
    return InventoryResponse(
        id=str(inventory.id),
        warehouse_id=inventory.warehouseId,
        product_id=inventory.productId,
        available_quantity=inventory.availableQuantity,
        reserved_quantity=inventory.reservedQuantity,
        outbound_transit_quantity=inventory.outboundTransitQuantity,
        inbound_transit_quantity=inventory.inboundTransitQuantity,
        last_updated_date=inventory.lastUpdatedDate,
        total_quantity=inventory.totalQuantity,
        product_name=product.name,
        product_code=product.code,
        warehouse_name=warehouse.name
    )


@router.post("/adjustment", response_model=InventoryMovementResponse)
async def adjust_inventory(
    adjustment: InventoryAdjustment,
    current_user: User = Depends(get_current_active_user)
):
    """Perform inventory adjustment"""
    
    try:
        # Perform adjustment using the service
        movement = await InventoryService.adjust_inventory(
            adjustment, str(current_user.id)
        )
        
        # Get additional information for the response
        product = await Product.get(adjustment.product_id)
        warehouse = await Warehouse.get(adjustment.warehouse_id)
        
        return InventoryMovementResponse(
            id=str(movement.id),
            warehouse_id=movement.warehouse_id,
            product_id=movement.product_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            previous_quantity=movement.previous_quantity,
            new_quantity=movement.new_quantity,
            user_id=movement.user_id,
            movement_date=movement.movement_date,
            reason=movement.reason,
            reference_id=movement.reference_id,
            reference_type=movement.reference_type,
            unit_cost=movement.unit_cost,
            total_value=movement.total_value,
            product_name=product.name if product else None,
            product_code=product.code if product else None,
            warehouse_name=warehouse.name if warehouse else None,
            user_name=f"{current_user.first_name} {current_user.last_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing adjustment: {str(e)}"
        )


@router.get("/movements", response_model=PaginatedResponse[InventoryMovementResponse])
async def list_inventory_movements(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    product_id: Optional[str] = Query(None, description="Filter by product"),
    movement_type: Optional[str] = Query(None, description="Filter by movement type"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    current_user: User = Depends(get_current_active_user)
):
    """List inventory movements with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if warehouse_id:
        query_params["warehouseId"] = warehouse_id
    
    if product_id:
        query_params["productId"] = product_id
    
    if movement_type:
        query_params["movementType"] = movement_type
    
    if user_id:
        query_params["userId"] = user_id
    
    # Aggregation pipeline to get related information
    pipeline = [
        {"$match": query_params},
        {"$sort": {"movementDate": -1}},
        {
            "$lookup": {
                "from": "products",
                "localField": "productId",
                "foreignField": "_id",
                "as": "product"
            }
        },
        {
            "$lookup": {
                "from": "warehouses",
                "localField": "warehouseId",
                "foreignField": "_id",
                "as": "warehouse"
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "userId",
                "foreignField": "_id",
                "as": "user"
            }
        }
    ]
    
    # Get total
    total_pipeline = pipeline + [{"$count": "total"}]
    total_result = await InventoryMovement.aggregate(total_pipeline).to_list()
    total_movements = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    movements = await InventoryMovement.aggregate(pipeline).to_list()
    
    # Convert to response
    movement_responses = []
    for mov in movements:
        product = mov.get("product", [{}])[0] if mov.get("product") else {}
        warehouse = mov.get("warehouse", [{}])[0] if mov.get("warehouse") else {}
        user = mov.get("user", [{}])[0] if mov.get("user") else {}
        
    movement_responses.append(InventoryMovementResponse(
            id=str(mov["_id"]),
            warehouse_id=mov["warehouse_id"],
            product_id=mov["product_id"],
            movement_type=mov["movement_type"],
            quantity=convert_decimal128_to_decimal(mov["quantity"]),
            previous_quantity=convert_decimal128_to_decimal(mov["previous_quantity"]),
            new_quantity=convert_decimal128_to_decimal(mov["new_quantity"]),
            user_id=mov["user_id"],
            movement_date=mov["movement_date"],
            reason=mov.get("reason"),
            reference_id=mov.get("referenceId"),
            reference_type=mov.get("referenceType"),
            unit_cost=convert_decimal128_to_decimal(mov.get("unitCost")),
            total_value=convert_decimal128_to_decimal(mov.get("totalValue")),
            product_name=product.get("name"),
            product_code=product.get("code"),
            warehouse_name=warehouse.get("name"),
            user_name=f"{user.get('fi   rstName', '')} {user.get('lastName', '')}".strip()
        ))
    
    total_pages = (total_movements + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=movement_responses,
        total=total_movements,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.get("/minimum-stock", response_model=List[dict])
async def get_minimum_stock_products(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    current_user: User = Depends(get_current_active_user)
):
    """Get products with stock below the minimum"""
    
    try:
        products = await InventoryService.get_minimum_stock_products(warehouse_id)
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting products with minimum stock: {str(e)}"
        )