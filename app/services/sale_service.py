from typing import List
from decimal import Decimal
from datetime import datetime
from fastapi import HTTPException, status

from app.models.sales import Sale, SaleDetail, Customer, PaymentMethod
from app.models.product import Product
from app.models.warehouses import Warehouse
from app.schemas.sale import SaleCreate, SaleDetailCreate
from app.services.inventory_service import InventoryService
from app.utils.generators import generate_sale_number


class SaleService:
    """Service for sales management"""
    
    @staticmethod
    async def create_sale(
        sale_data: SaleCreate,
        user_id: str
    ) -> Sale:
        """Create a new sale"""
        
        # Validate warehouse
        warehouse = await Warehouse.get(sale_data.warehouse_id)
        if not warehouse or not warehouse.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found or inactive"
            )
        
        # Validate customer if provided
        if sale_data.customer_id:
            customer = await Customer.get(sale_data.customer_id)
            if not customer or not customer.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found or inactive"
                )
        
        # Validate payment method
        payment_method = await PaymentMethod.get(sale_data.payment_method_id)
        if not payment_method or not payment_method.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found or inactive"
            )
        
        # Validate and reserve stock for all products
        processed_details = []
        reserved_products = []
        
        try:
            for detail in sale_data.details:
                # Validate product
                product = await Product.get(detail.product_id)
                if not product or not product.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product {detail.product_id} not found or inactive"
                    )
                
                # Check available stock
                if not await InventoryService.check_availability(
                    sale_data.warehouse_id, 
                    detail.product_id, 
                    detail.quantity
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for product {product.name}"
                    )
                
                # Reserve stock
                if not await InventoryService.reserve_stock(
                    sale_data.warehouse_id,
                    detail.product_id,
                    detail.quantity
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Could not reserve stock for {product.name}"
                    )
                
                reserved_products.append({
                    "product_id": detail.product_id,
                    "quantity": detail.quantity
                })
                
                # Calculate detail totals
                subtotal = detail.quantity * detail.unit_price
                detail_total = subtotal - detail.discount
                
                sale_detail = SaleDetail(
                    product_id=detail.product_id,
                    product_code=product.code,
                    product_name=product.name,
                    quantity=detail.quantity,
                    unit_price=detail.unit_price,
                    subtotal=subtotal,
                    discount=detail.discount,
                    total=detail_total
                )
                processed_details.append(sale_detail)
            
            # Calculate sale totals
            sale_subtotal = sum(d.subtotal for d in processed_details)
            sale_total = sale_subtotal - sale_data.discount
            
            # Calculate change if cash payment
            change = None
            if (sale_data.amount_received and 
                sale_data.amount_received > sale_total):
                change = sale_data.amount_received - sale_total
            
            # Create sale
            sale = Sale(
                sale_number=await generate_sale_number(),
                warehouse_id=sale_data.warehouse_id,
                customer_id=sale_data.customer_id,
                user_id=user_id,
                payment_method_id=sale_data.payment_method_id,
                details=processed_details,
                subtotal=sale_subtotal,
                discount=sale_data.discount,
                tax=Decimal("0"),  # TODO: Implement tax calculation
                total=sale_total,
                observations=sale_data.observations,
                payment_reference=sale_data.payment_reference,
                amount_received=sale_data.amount_received,
                change=change
            )
            
            await sale.insert()
            
            # Confirm sale in inventory (convert reserved to sold)
            for detail in processed_details:
                await InventoryService.confirm_sale_stock(
                    sale_data.warehouse_id,
                    detail.product_id,
                    detail.quantity,
                    user_id,
                    str(sale.id)
                )
            
            return sale
            
        except Exception as e:
            # If error, release reserved stock
            for item in reserved_products:
                await InventoryService.release_reserved_stock(
                    sale_data.warehouse_id,
                    item["product_id"],
                    item["quantity"]
                )
            raise e
    
    @staticmethod
    async def cancel_sale(sale_id: str, user_id: str) -> Sale:
        """Cancel a sale and restore stock"""
        sale = await Sale.get(sale_id)
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )
        
        if sale.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sale is already cancelled"
            )
        
        # Restore stock
        for detail in sale.details:
            await InventoryService.update_stock(
                warehouse_id=sale.warehouse_id,
                product_id=detail.product_id,
                quantity=detail.quantity,
                movement_type="inbound",
                user_id=user_id,
                reference_id=str(sale.id),
                reference_type="cancelled_sale",
                reason="Sale cancellation"
            )
        
        # Update status
        sale.status = "cancelled"
        await sale.save()
        
        return sale
    
    @staticmethod
    async def get_sales_by_period(
        warehouse_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Sale]:
        """Get sales by period"""
        return await Sale.find({
            "warehouse_id": warehouse_id,
            "sale_date": {
                "$gte": start_date,
                "$lte": end_date
            },
            "status": {"$ne": "cancelled"}
        }).to_list()
    
    @staticmethod
    async def calculate_daily_sales_total(
        warehouse_id: str,
        date: datetime
    ) -> dict:
        """Calculate daily sales totals"""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        pipeline = [
            {
                "$match": {
                    "warehouse_id": warehouse_id,
                    "sale_date": {"$gte": day_start, "$lte": day_end},
                    "status": {"$ne": "cancelled"}
                }
            },
            {
                "$group": {
                    "_id": "$payment_method_id",
                    "total": {"$sum": "$total"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await Sale.aggregate(pipeline).to_list()
        
        total_general = sum(r["total"] for r in results)
        count_general = sum(r["count"] for r in results)
        
        return {
            "total_sales": total_general,
            "sales_count": count_general,
            "by_payment_method": results,
            "average_ticket": total_general / count_general if count_general > 0 else 0
        }
    
    @staticmethod
    async def get_best_selling_products(
        warehouse_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[dict]:
        """Get best selling products in a period"""
        pipeline = [
            {
                "$match": {
                    "warehouse_id": warehouse_id,
                    "sale_date": {"$gte": start_date, "$lte": end_date},
                    "status": {"$ne": "cancelled"}
                }
            },
            {"$unwind": "$details"},
            {
                "$group": {
                    "_id": "$details.product_id",
                    "product_name": {"$first": "$details.product_name"},
                    "product_code": {"$first": "$details.product_code"},
                    "quantity_sold": {"$sum": "$details.quantity"},
                    "revenue": {"$sum": "$details.total"}
                }
            },
            {"$sort": {"quantity_sold": -1}},
            {"$limit": limit}
        ]
        
        return await Sale.aggregate(pipeline).to_list()