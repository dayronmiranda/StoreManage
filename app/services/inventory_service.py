from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.inventories import Inventory, InventoryMovement
from app.models.product import Product
from app.models.warehouses import Warehouse
from app.schemas.inventory import InventoryAdjustment


class InventoryService:
    """Service for inventory management"""
    
    @staticmethod
    async def check_availability(
        warehouse_id: str, 
        product_id: str, 
        quantity: Decimal
    ) -> bool:
        """Check if stock is available"""
        inventory = await Inventory.find_one({
            "warehouse_id": warehouse_id,
            "product_id": product_id
        })
        
        if not inventory:
            return False
        
        return inventory.available_quantity >= quantity
    
    @staticmethod
    async def get_inventory(
        warehouse_id: str, 
        product_id: str
    ) -> Optional[Inventory]:
        """Get specific inventory"""
        return await Inventory.find_one({
            "warehouse_id": warehouse_id,
            "product_id": product_id
        })
    
    @staticmethod
    async def create_or_update_inventory(
        warehouse_id: str,
        product_id: str,
        initial_quantity: Decimal = Decimal("0")
    ) -> Inventory:
        """Create or get existing inventory"""
        inventory = await InventoryService.get_inventory(warehouse_id, product_id)
        
        if not inventory:
            # Verify warehouse and product exist
            warehouse = await Warehouse.get(warehouse_id)
            if not warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found"
                )
            
            product = await Product.get(product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            inventory = Inventory(
                warehouse_id=warehouse_id,
                product_id=product_id,
                available_quantity=initial_quantity
            )
            await inventory.insert()
        
        return inventory
    
    @staticmethod
    async def update_stock(
        warehouse_id: str,
        product_id: str,
        quantity: Decimal,
        movement_type: str,
        user_id: str,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        reason: Optional[str] = None,
        unit_cost: Optional[Decimal] = None
    ) -> InventoryMovement:
        """Update stock and create movement"""
        
        # Get or create inventory
        inventory = await InventoryService.create_or_update_inventory(
            warehouse_id, product_id
        )
        
        previous_quantity = inventory.available_quantity
        
        # Calculate new quantity based on movement type
        if movement_type in ["inbound", "transfer_inbound"]:
            new_quantity = previous_quantity + quantity
        elif movement_type in ["outbound", "transfer_outbound"]:
            new_quantity = previous_quantity - quantity
            if new_quantity < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient stock"
                )
        elif movement_type == "adjustment":
            new_quantity = quantity
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid movement type"
            )
        
        # Update inventory
        inventory.available_quantity = new_quantity
        inventory.updated_at = datetime.utcnow()
        await inventory.save()
        
        # Create movement
        movement = InventoryMovement(
            warehouse_id=warehouse_id,
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            user_id=user_id,
            reference_id=reference_id,
            reference_type=reference_type,
            reason=reason,
            unit_cost=unit_cost,
            total_value=unit_cost * quantity if unit_cost else None
        )
        await movement.insert()
        
        return movement
    
    @staticmethod
    async def adjust_inventory(
        adjustment: InventoryAdjustment,
        user_id: str
    ) -> InventoryMovement:
        """Perform inventory adjustment"""
        return await InventoryService.update_stock(
            warehouse_id=adjustment.warehouse_id,
            product_id=adjustment.product_id,
            quantity=adjustment.new_quantity,
            movement_type="adjustment",
            user_id=user_id,
            reason=adjustment.reason
        )
    
    @staticmethod
    async def reserve_stock(
        warehouse_id: str,
        product_id: str,
        quantity: Decimal
    ) -> bool:
        """Reserve stock for a sale"""
        inventory = await InventoryService.get_inventory(warehouse_id, product_id)
        
        if not inventory or inventory.available_quantity < quantity:
            return False
        
        inventory.available_quantity -= quantity
        inventory.reserved_quantity += quantity
        inventory.updated_at = datetime.utcnow()
        await inventory.save()
        
        return True
    
    @staticmethod
    async def release_reserved_stock(
        warehouse_id: str,
        product_id: str,
        quantity: Decimal
    ) -> bool:
        """Release reserved stock"""
        inventory = await InventoryService.get_inventory(warehouse_id, product_id)
        
        if not inventory or inventory.reserved_quantity < quantity:
            return False
        
        inventory.reserved_quantity -= quantity
        inventory.available_quantity += quantity
        inventory.updated_at = datetime.utcnow()
        await inventory.save()
        
        return True
    
    @staticmethod
    async def confirm_sale_stock(
        warehouse_id: str,
        product_id: str,
        quantity: Decimal,
        user_id: str,
        sale_id: str
    ) -> InventoryMovement:
        """Confirm sale and reduce reserved stock"""
        inventory = await InventoryService.get_inventory(warehouse_id, product_id)
        
        if not inventory or inventory.reserved_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient reserved stock"
            )
        
        previous_quantity = inventory.reserved_quantity + inventory.available_quantity
        
        # Reduce reserved stock
        inventory.reserved_quantity -= quantity
        inventory.updated_at = datetime.utcnow()
        await inventory.save()
        
        # Create outbound movement
        movement = InventoryMovement(
            warehouse_id=warehouse_id,
            product_id=product_id,
            movement_type="outbound",
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=inventory.available_quantity + inventory.reserved_quantity,
            user_id=user_id,
            reference_id=sale_id,
            reference_type="sale",
            reason="Sale confirmed"
        )
        await movement.insert()
        
        return movement
    
    @staticmethod
    async def get_minimum_stock_products(warehouse_id: Optional[str] = None) -> List[dict]:
        """Get products with stock below minimum"""
        pipeline = [
            {
                "$addFields": {
                    "product_id_obj": {"$toObjectId": "$product_id"}
                }
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "product_id_obj",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$ne": ["$product.minimum_stock", None]},
                            {"$lt": ["$available_quantity", "$product.minimum_stock"]}
                        ]
                    }
                }
            }
        ]
        
        if warehouse_id:
            pipeline.insert(0, {"$match": {"warehouse_id": warehouse_id}})
        
        return await Inventory.aggregate(pipeline).to_list()