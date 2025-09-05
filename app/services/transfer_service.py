from typing import List
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException, status

from app.models.transfers import Transfer, TransferDetail, GoodsInTransit
from app.models.products import Product
from app.models.warehouses import Warehouse
from app.schemas.transfer import (
    TransferCreate, 
    ApproveTransfer,
    DispatchTransfer,
    ReceiveTransfer
)
from app.services.inventory_service import InventoryService
from app.utils.generators import generate_transfer_number


class TransferService:
    """Service for transfer management"""
    
    @staticmethod
    async def create_transfer(
        transfer_data: TransferCreate,
        user_id: str
    ) -> Transfer:
        """Create a new transfer"""
        
        # Validate warehouses
        source_warehouse = await Warehouse.get(transfer_data.source_warehouse_id)
        if not source_warehouse or not source_warehouse.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source warehouse not found or inactive"
            )
        
        destination_warehouse = await Warehouse.get(transfer_data.destination_warehouse_id)
        if not destination_warehouse or not destination_warehouse.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination warehouse not found or inactive"
            )
        
        # Don't allow transfer to same warehouse
        if transfer_data.source_warehouse_id == transfer_data.destination_warehouse_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer to the same warehouse"
            )
        
        # Validate products and stock
        processed_details = []
        
        for detail in transfer_data.details:
            # Validate product
            product = await Product.get(detail.product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {detail.product_id} not found or inactive"
                )
            
            # Check available stock in source warehouse
            if not await InventoryService.check_availability(
                transfer_data.source_warehouse_id,
                detail.product_id,
                detail.requested_quantity
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product {product.name}"
                )
            
            transfer_detail = TransferDetail(
                product_id=detail.product_id,
                product_code=product.code,
                product_name=product.name,
                requested_quantity=detail.requested_quantity,
                transit_quantity=Decimal("0")
            )
            processed_details.append(transfer_detail)
        
        # Create transfer
        transfer = Transfer(
            transfer_number=await generate_transfer_number(),
            source_warehouse_id=transfer_data.source_warehouse_id,
            destination_warehouse_id=transfer_data.destination_warehouse_id,
            requested_by_user_id=user_id,
            status="pending",
            details=processed_details,
            estimated_arrival_date=transfer_data.estimated_arrival_date,
            carrier=transfer_data.carrier,
            reason=transfer_data.reason,
            notes=transfer_data.observations,
            priority=transfer_data.priority
        )
        
        await transfer.insert()
        return transfer
    
    @staticmethod
    async def approve_transfer(
        transfer_id: str,
        user_id: str,
        approval_data: ApproveTransfer
    ) -> Transfer:
        """Approve transfer"""
        
        transfer = await Transfer.get(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending transfers can be approved"
            )
        
        # Check stock again
        for detail in transfer.details:
            if not await InventoryService.check_availability(
                transfer.source_warehouse_id,
                detail.product_id,
                detail.requested_quantity
            ):
                product = await Product.get(detail.product_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product {product.name}"
                )
        
        # Update transfer
        transfer.status = "approved"
        transfer.approved_by_user_id = user_id
        transfer.approval_date = datetime.utcnow()
        if approval_data.observations:
            transfer.notes = approval_data.observations
        
        await transfer.save()
        return transfer
    
    @staticmethod
    async def reject_transfer(
        transfer_id: str,
        user_id: str,
        reason: str
    ) -> Transfer:
        """Reject transfer"""
        
        transfer = await Transfer.get(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending transfers can be rejected"
            )
        
        # Update transfer
        transfer.status = "rejected"
        transfer.approved_by_user_id = user_id
        transfer.approval_date = datetime.utcnow()
        transfer.notes = reason
        
        await transfer.save()
        return transfer
    
    @staticmethod
    async def dispatch_transfer(
        transfer_id: str,
        user_id: str,
        dispatch_data: DispatchTransfer
    ) -> Transfer:
        """Dispatch transfer (outbound from source warehouse)"""
        
        transfer = await Transfer.get(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only approved transfers can be dispatched"
            )
        
        # Reserve and move stock from source warehouse
        for detail in transfer.details:
            # Update source inventory (outbound)
            await InventoryService.update_stock(
                warehouse_id=transfer.source_warehouse_id,
                product_id=detail.product_id,
                quantity=detail.requested_quantity,
                movement_type="transfer_outbound",
                user_id=user_id,
                reference_id=str(transfer.id),
                reference_type="transfer",
                reason=f"Transfer to {transfer.destination_warehouse_id}"
            )
            
            # Update detail
            detail.sent_quantity = detail.requested_quantity
            detail.transit_quantity = detail.requested_quantity
        
        # Update transfer
        transfer.status = "in_transit"
        transfer.dispatched_by_user_id = user_id
        transfer.departure_date = datetime.utcnow()
        transfer.tracking_number = dispatch_data.transport_guide
        transfer.transport_cost = dispatch_data.transport_cost
        if dispatch_data.observations:
            transfer.notes = dispatch_data.observations
        
        await transfer.save()
        
        # Create transit record
        transit = GoodsInTransit(
            transfer_id=str(transfer.id),
            transit_status="preparing",
            updated_by=user_id,
            notes="Transfer dispatched from source warehouse"
        )
        await transit.insert()
        
        return transfer
    
    @staticmethod
    async def receive_transfer(
        transfer_id: str,
        user_id: str,
        reception_data: ReceiveTransfer
    ) -> Transfer:
        """Receive transfer (inbound to destination warehouse)"""
        
        transfer = await Transfer.get(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status != "in_transit":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only transfers in transit can be received"
            )
        
        # Process reception of each product
        for received_detail in reception_data.received_details:
            # Find corresponding detail
            transfer_detail = None
            for detail in transfer.details:
                if detail.product_id == received_detail["product_id"]:
                    transfer_detail = detail
                    break
            
            if not transfer_detail:
                continue
            
            received_quantity = Decimal(str(received_detail["received_quantity"]))
            
            # Update destination inventory (inbound)
            await InventoryService.update_stock(
                warehouse_id=transfer.destination_warehouse_id,
                product_id=transfer_detail.product_id,
                quantity=received_quantity,
                movement_type="transfer_inbound",
                user_id=user_id,
                reference_id=str(transfer.id),
                reference_type="transfer",
                reason=f"Transfer from {transfer.source_warehouse_id}"
            )
            
            # Update detail
            transfer_detail.received_quantity = received_quantity
            transfer_detail.transit_quantity = Decimal("0")
            
            # Calculate discrepancy
            if received_quantity != transfer_detail.sent_quantity:
                transfer_detail.discrepancy = (
                    received_quantity - transfer_detail.sent_quantity
                )
                transfer_detail.discrepancy_note = (
                    received_detail.get("observation", "")
                )
        
        # Update transfer
        transfer.status = "completed"
        transfer.received_by_user_id = user_id
        transfer.actual_arrival_date = datetime.utcnow()
        transfer.completed_date = datetime.utcnow()
        if reception_data.observations:
            transfer.notes = reception_data.observations
        
        await transfer.save()
        
        # Update transit record
        transit = await GoodsInTransit.find_one({"transfer_id": str(transfer.id)})
        if transit:
            transit.transit_status = "delivered"
            transit.updated_by = user_id
            transit.updated_at = datetime.utcnow()
            transit.notes = "Transfer received at destination warehouse"
            await transit.save()
        
        return transfer
    
    @staticmethod
    async def cancel_transfer(
        transfer_id: str,
        user_id: str,
        reason: str
    ) -> Transfer:
        """Cancel transfer"""
        
        transfer = await Transfer.get(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        if transfer.status in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a completed or already cancelled transfer"
            )
        
        # If in transit, restore stock at source
        if transfer.status == "in_transit":
            for detail in transfer.details:
                if detail.sent_quantity and detail.sent_quantity > 0:
                    await InventoryService.update_stock(
                        warehouse_id=transfer.source_warehouse_id,
                        product_id=detail.product_id,
                        quantity=detail.sent_quantity,
                        movement_type="inbound",
                        user_id=user_id,
                        reference_id=str(transfer.id),
                        reference_type="cancelled_transfer",
                        reason="Transfer cancellation"
                    )
        
        # Update transfer
        transfer.status = "cancelled"
        transfer.notes = reason
        
        await transfer.save()
        return transfer