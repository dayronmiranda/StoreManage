from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.models.financials import CashCut, OperationalExpense, CashMovement
from app.models.sales import Sale
from app.models.warehouses import Warehouse
from app.services.sale_service import SaleService


class CashCutService:
    """Service for cash cut management"""
    
    @staticmethod
    async def open_cash_cut(
        warehouse_id: str,
        user_id: str,
        initial_amount: Decimal,
        cut_date: Optional[datetime] = None
    ) -> CashCut:
        """Open new cash cut"""
        
        if not cut_date:
            cut_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Verify warehouse exists
        warehouse = await Warehouse.get(warehouse_id)
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found"
            )
        
        # Verify there's no open cut for this warehouse
        open_cut = await CashCut.find_one({
            "warehouseId": warehouse_id,
            "status": "open"
        })
        
        if open_cut:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There's already an open cash cut for this warehouse"
            )
        
        # Create cash cut
        cut = CashCut(
            warehouseId=warehouse_id,
            userId=user_id,
            cutDate=cut_date,
            openingTime=datetime.utcnow(),
            initialAmount=initial_amount,
            status="open"
        )
        
        await cut.insert()
        
        # Create initial movement
        movement = CashMovement(
            warehouseId=warehouse_id,
            cashCutId=str(cut.id),
            movementType="inbound",
            concept="initial_fund",
            amount=initial_amount,
            userId=user_id,
            notes="Cash opening"
        )
        await movement.insert()
        
        return cut
    
    @staticmethod
    async def close_cash_cut(
        cut_id: str,
        user_id: str,
        actual_final_amount: Decimal,
        observations: Optional[str] = None
    ) -> CashCut:
        """Close cash cut"""
        
        cut = await CashCut.get(cut_id)
        if not cut:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash cut not found"
            )
        
        if cut.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cash cut is already closed"
            )
        
        # Calculate daily totals
        day_start = cut.cutDate
        day_end = day_start + timedelta(days=1)
        
        # Get daily sales
        sales_report = await SaleService.calculate_daily_sales_total(
            cut.warehouseId, cut.cutDate
        )
        
        # Get daily expenses
        daily_expenses = await OperationalExpense.find({
            "warehouseId": cut.warehouseId,
            "expenseDate": {"$gte": day_start, "$lt": day_end},
            "status": "approved"
        }).to_list()
        
        total_expenses = sum(expense.amount for expense in daily_expenses)
        
        # Calculate expected final amount
        expected_final_amount = (
            cut.initialAmount + 
            sales_report["total_sales"] - 
            total_expenses
        )
        
        # Calculate difference
        difference = actual_final_amount - expected_final_amount
        
        # Update cut
        cut.closingTime = datetime.utcnow()
        cut.cashSales = sales_report.get("by_payment_method", {}).get("cash", Decimal("0"))
        cut.totalSales = sales_report["total_sales"]
        cut.totalExpenses = total_expenses
        cut.expectedFinalAmount = expected_final_amount
        cut.actualFinalAmount = actual_final_amount
        cut.difference = difference
        cut.notes = observations
        cut.status = "closed"
        cut.transactionCount = sales_report["sales_count"]
        cut.averageTicket = sales_report["average_ticket"]
        
        await cut.save()
        
        return cut
    
    @staticmethod
    async def get_current_cut(warehouse_id: str) -> Optional[CashCut]:
        """Get current (open) cash cut for a warehouse"""
        
        return await CashCut.find_one({
            "warehouseId": warehouse_id,
            "status": "open"
        })
    
    @staticmethod
    async def register_cash_movement(
        warehouse_id: str,
        movement_type: str,
        concept: str,
        amount: Decimal,
        user_id: str,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        observations: Optional[str] = None
    ) -> CashMovement:
        """Register cash movement"""
        
        # Get current cut
        current_cut = await CashCutService.get_current_cut(warehouse_id)
        
        # Create movement
        movement = CashMovement(
            warehouseId=warehouse_id,
            cashCutId=str(current_cut.id) if current_cut else None,
            movementType=movement_type,
            concept=concept,
            amount=amount,
            referenceId=reference_id,
            referenceType=reference_type,
            userId=user_id,
            notes=observations
        )
        
        await movement.insert()
        return movement
    
    @staticmethod
    async def get_cash_summary(
        warehouse_id: str,
        date: Optional[datetime] = None
    ) -> dict:
        """Get daily cash summary"""
        
        if not date:
            date = datetime.now()
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # Get current cut
        current_cut = await CashCutService.get_current_cut(warehouse_id)
        
        # Get daily movements
        movements = await CashMovement.find({
            "warehouseId": warehouse_id,
            "movementDate": {"$gte": day_start, "$lt": day_end}
        }).to_list()
        
        # Calculate totals
        total_inbound = sum(
            mov.amount for mov in movements 
            if mov.movementType == "inbound"
        )
        
        total_outbound = sum(
            mov.amount for mov in movements 
            if mov.movementType == "outbound"
        )
        
        # Get daily sales
        sales_report = await SaleService.calculate_daily_sales_total(warehouse_id, date)
        
        return {
            "current_cut": current_cut,
            "total_inbound": total_inbound,
            "total_outbound": total_outbound,
            "current_balance": total_inbound - total_outbound,
            "daily_sales": sales_report,
            "movements_count": len(movements)
        }