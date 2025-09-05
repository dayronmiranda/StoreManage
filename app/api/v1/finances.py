from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.financials import OperationalExpense, ExpenseCategory, CashCut, CashMovement
from app.models.warehouses import Warehouse
from app.models.user import User
from app.schemas.financial import (
    OperationalExpenseCreate,
    OperationalExpenseUpdate,
    OperationalExpenseResponse,
    OperationalExpenseListResponse,
    ApproveExpense,
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryResponse,
    CashCutCreate,
    CashCutResponse,
    CashCutListResponse,
    CloseCashCut,
    CashMovementResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.services.cash_cut_service import CashCutService

router = APIRouter(prefix="/finances", tags=["Finances"])


# OPERATIONAL EXPENSES ENDPOINTS
@router.get("/expenses", response_model=PaginatedResponse[OperationalExpenseListResponse])
async def list_expenses(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    expense_category_id: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_active_user)
):
    """List operational expenses with pagination and filters"""
    
    # Build query
    query = {}
    
    if warehouse_id:
        query["warehouseId"] = warehouse_id
    
    if expense_category_id:
        query["expenseCategoryId"] = expense_category_id
    
    if status:
        query["status"] = status
    
    if user_id:
        query["userId"] = user_id
    
    # Date filter
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["expenseDate"] = date_query
    
    # Aggregation pipeline to get related information
    pipeline = [
        {"$match": query},
        {"$sort": {"expenseDate": -1}},
        {
            "$lookup": {
                "from": "expense_categories",
                "localField": "expenseCategoryId",
                "foreignField": "_id",
                "as": "category"
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
    total_result = await OperationalExpense.aggregate(total_pipeline).to_list()
    total = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    expenses = await OperationalExpense.aggregate(pipeline).to_list()
    
    # Convert to response
    expenses_response = []
    for expense in expenses:
        category = expense.get("category", [{}])[0] if expense.get("category") else {}
        warehouse = expense.get("warehouse", [{}])[0] if expense.get("warehouse") else {}
        
        expenses_response.append(OperationalExpenseListResponse(
            id=str(expense["_id"]),
            expense_date=expense["expenseDate"],
            description=expense["description"],
            amount=expense["amount"],
            status=expense["status"],
            category_name=category.get("name"),
            warehouse_name=warehouse.get("name")
        ))
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=expenses_response,
        total=total,
        page=pagination.page,
        pages=pages,
        size=pagination.size,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post("/expenses", response_model=OperationalExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: OperationalExpenseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new operational expense"""
    
    # Validate warehouse
    warehouse = await Warehouse.get(expense_data.warehouse_id)
    if not warehouse or not warehouse.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found or inactive"
        )
    
    # Validate category
    category = await ExpenseCategory.get(expense_data.expense_category_id)
    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found or inactive"
        )
    
    # Create expense
    expense = OperationalExpense(
        warehouseId=expense_data.warehouse_id,
        expenseCategoryId=expense_data.expense_category_id,
        description=expense_data.description,
        amount=expense_data.amount,
        expenseDate=expense_data.expense_date,
        userId=str(current_user.id),
        receiptNumber=expense_data.receipt_number,
        supplier=expense_data.supplier,
        paymentMethod=expense_data.payment_method,
        paymentReference=expense_data.payment_reference,
        notes=expense_data.observations,
        status="pending"
    )
    
    await expense.insert()
    
    return OperationalExpenseResponse(
        id=str(expense.id),
        warehouse_id=expense.warehouseId,
        expense_category_id=expense.expenseCategoryId,
        description=expense.description,
        amount=expense.amount,
        expense_date=expense.expenseDate,
        user_id=expense.userId,
        image_path=expense.imagePath,
        receipt_number=expense.receiptNumber,
        supplier=expense.supplier,
        status=expense.status,
        approved_by=expense.approvedBy,
        approval_date=expense.approvalDate,
        payment_method=expense.paymentMethod,
        payment_reference=expense.paymentReference,
        observations=expense.notes,
        category_name=category.name,
        warehouse_name=warehouse.name,
        user_name=f"{current_user.first_name} {current_user.last_name}"
    )


@router.get("/expenses/{expense_id}", response_model=OperationalExpenseResponse)
async def get_expense(
    expense_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get expense by ID"""
    
    try:
        expense = await OperationalExpense.get(PydanticObjectId(expense_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # Get related information
    category = await ExpenseCategory.get(expense.expenseCategoryId)
    warehouse = await Warehouse.get(expense.warehouseId)
    user = await User.get(expense.userId)
    
    return OperationalExpenseResponse(
        id=str(expense.id),
        warehouse_id=expense.warehouseId,
        expense_category_id=expense.expenseCategoryId,
        description=expense.description,
        amount=expense.amount,
        expense_date=expense.expenseDate,
        user_id=expense.userId,
        image_path=expense.imagePath,
        receipt_number=expense.receiptNumber,
        supplier=expense.supplier,
        status=expense.status,
        approved_by=expense.approvedBy,
        approval_date=expense.approvalDate,
        payment_method=expense.paymentMethod,
        payment_reference=expense.paymentReference,
        observations=expense.notes,
        category_name=category.name if category else None,
        warehouse_name=warehouse.name if warehouse else None,
        user_name=f"{user.first_name} {user.last_name}" if user else None
    )


@router.patch("/expenses/{expense_id}/approve")
async def approve_expense(
    expense_id: str,
    approval_data: ApproveExpense,
    current_user: User = Depends(get_current_active_user)
):
    """Approve operational expense"""
    
    try:
        expense = await OperationalExpense.get(PydanticObjectId(expense_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    if expense.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending expenses can be approved"
        )
    
    # Approve expense
    expense.status = "approved"
    expense.approvedBy = str(current_user.id)
    expense.approvalDate = datetime.utcnow()
    if approval_data.observations:
        expense.notes = approval_data.observations
    
    await expense.save()
    
    # Register cash movement
    await CashCutService.register_cash_movement(
        warehouse_id=expense.warehouseId,
        movement_type="outbound",
        concept="operational_expense",
        amount=expense.amount,
        user_id=str(current_user.id),
        reference_id=str(expense.id),
        reference_type="expense",
        observations=f"Approved expense: {expense.description}"
    )
    
    return {
        "message": "Expense approved successfully",
        "amount": expense.amount
    }


@router.patch("/expenses/{expense_id}/reject")
async def reject_expense(
    expense_id: str,
    reason: str,
    current_user: User = Depends(get_current_active_user)
):
    """Reject operational expense"""
    
    try:
        expense = await OperationalExpense.get(PydanticObjectId(expense_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    if expense.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending expenses can be rejected"
        )
    
    # Reject expense
    expense.status = "rejected"
    expense.approvedBy = str(current_user.id)
    expense.approvalDate = datetime.utcnow()
    expense.notes = reason
    
    await expense.save()
    
    return {
        "message": "Expense rejected successfully"
    }


# CASH CUT ENDPOINTS
@router.get("/cash-cuts", response_model=PaginatedResponse[CashCutListResponse])
async def list_cash_cuts(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_active_user)
):
    """List cash cuts with pagination and filters"""
    
    # Build query
    query = {}
    
    if warehouse_id:
        query["warehouseId"] = warehouse_id
    
    if status:
        query["status"] = status
    
    # Date filter
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["cutDate"] = date_query
    
    # Aggregation pipeline
    pipeline = [
        {"$match": query},
        {"$sort": {"cutDate": -1}},
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
    total_result = await CashCut.aggregate(total_pipeline).to_list()
    total = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    cuts = await CashCut.aggregate(pipeline).to_list()
    
    # Convert to response
    cuts_response = []
    for cut in cuts:
        warehouse = cut.get("warehouse", [{}])[0] if cut.get("warehouse") else {}
        
        cuts_response.append(CashCutListResponse(
            id=str(cut["_id"]),
            cut_date=cut["cutDate"],
            warehouse_name=warehouse.get("name"),
            total_sales=cut["totalSales"],
            status=cut["status"],
            difference=cut.get("difference")
        ))
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=cuts_response,
        total=total,
        page=pagination.page,
        pages=pages,
        size=pagination.size,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post("/cash-cuts", response_model=CashCutResponse, status_code=status.HTTP_201_CREATED)
async def open_cash_cut(
    cut_data: CashCutCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Open new cash cut"""
    
    try:
        cut = await CashCutService.open_cash_cut(
            warehouse_id=cut_data.warehouse_id,
            user_id=str(current_user.id),
            initial_amount=cut_data.initial_amount,
            cut_date=cut_data.cut_date
        )
        
        # Get related information
        warehouse = await Warehouse.get(cut.warehouseId)
        
        return CashCutResponse(
            id=str(cut.id),
            warehouse_id=cut.warehouseId,
            user_id=cut.userId,
            cut_date=cut.cutDate,
            opening_time=cut.openingTime,
            closing_time=cut.closingTime,
            initial_amount=cut.initialAmount,
            cash_sales=cut.cashSales,
            total_sales=cut.totalSales,
            total_expenses=cut.totalExpenses,
            expected_final_amount=cut.expectedFinalAmount,
            actual_final_amount=cut.actualFinalAmount,
            difference=cut.difference,
            observations=cut.notes,
            status=cut.status,
            card_sales=cut.cardSales,
            transfer_sales=cut.transferSales,
            transaction_count=cut.transactionCount,
            average_ticket=cut.averageTicket,
            warehouse_name=warehouse.name if warehouse else None,
            user_name=f"{current_user.first_name} {current_user.last_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error opening cash cut: {str(e)}"
        )


@router.patch("/cash-cuts/{cut_id}/close")
async def close_cash_cut(
    cut_id: str,
    closing_data: CloseCashCut,
    current_user: User = Depends(get_current_active_user)
):
    """Close cash cut"""
    
    try:
        cut = await CashCutService.close_cash_cut(
            cut_id=cut_id,
            user_id=str(current_user.id),
            actual_final_amount=closing_data.actual_final_amount,
            observations=closing_data.observations
        )
        
        return {
            "message": "Cash cut closed successfully",
            "difference": cut.difference,
            "total_sales": cut.totalSales
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing cash cut: {str(e)}"
        )


@router.get("/cash-cuts/{cut_id}", response_model=CashCutResponse)
async def get_cash_cut(
    cut_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get cash cut by ID"""
    
    try:
        cut = await CashCut.get(PydanticObjectId(cut_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cash cut not found"
        )
    
    if not cut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cash cut not found"
        )
    
    # Get related information
    warehouse = await Warehouse.get(cut.warehouseId)
    user = await User.get(cut.userId)
    
    return CashCutResponse(
        id=str(cut.id),
        warehouse_id=cut.warehouseId,
        user_id=cut.userId,
        cut_date=cut.cutDate,
        opening_time=cut.openingTime,
        closing_time=cut.closingTime,
        initial_amount=cut.initialAmount,
        cash_sales=cut.cashSales,
        total_sales=cut.totalSales,
        total_expenses=cut.totalExpenses,
        expected_final_amount=cut.expectedFinalAmount,
        actual_final_amount=cut.actualFinalAmount,
        difference=cut.difference,
        observations=cut.notes,
        status=cut.status,
        card_sales=cut.cardSales,
        transfer_sales=cut.transferSales,
        transaction_count=cut.transactionCount,
        average_ticket=cut.averageTicket,
        warehouse_name=warehouse.name if warehouse else None,
        user_name=f"{user.first_name} {user.last_name}" if user else None
    )


@router.get("/cash-cuts/current/{warehouse_id}")
async def get_current_cash_cut(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get current (open) cash cut for a warehouse"""
    
    cut = await CashCutService.get_current_cut(warehouse_id)
    
    if not cut:
        return {"message": "No open cash cut", "cut": None}
    
    # Get related information
    warehouse = await Warehouse.get(cut.warehouseId)
    user = await User.get(cut.userId)
    
    return {
        "message": "Current cash cut found",
        "cut": CashCutResponse(
            id=str(cut.id),
            warehouse_id=cut.warehouseId,
            user_id=cut.userId,
            cut_date=cut.cutDate,
            opening_time=cut.openingTime,
            closing_time=cut.closingTime,
            initial_amount=cut.initialAmount,
            cash_sales=cut.cashSales,
            total_sales=cut.totalSales,
            total_expenses=cut.totalExpenses,
            expected_final_amount=cut.expectedFinalAmount,
            actual_final_amount=cut.actualFinalAmount,
            difference=cut.difference,
            observations=cut.notes,
            status=cut.status,
            card_sales=cut.cardSales,
            transfer_sales=cut.transferSales,
            transaction_count=cut.transactionCount,
            average_ticket=cut.averageTicket,
            warehouse_name=warehouse.name if warehouse else None,
            user_name=f"{user.first_name} {user.last_name}" if user else None
        )
    }


@router.get("/cash-summary/{warehouse_id}")
async def get_cash_summary(
    warehouse_id: str,
    date: Optional[datetime] = Query(None, description="Date (default today)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily cash summary"""
    
    try:
        summary = await CashCutService.get_cash_summary(warehouse_id, date)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cash summary: {str(e)}"
        )


# EXPENSE CATEGORIES ENDPOINTS
@router.get("/expense-categories", response_model=List[ExpenseCategoryResponse])
async def list_expense_categories(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List expense categories"""
    
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    categories = await ExpenseCategory.find(query).to_list()
    
    return [
        ExpenseCategoryResponse(
            id=str(category.id),
            name=category.name,
            description=category.description,
            is_active=category.is_active,
            code=category.code
        )
        for category in categories
    ]


@router.post("/expense-categories", response_model=ExpenseCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_expense_category(
    category_data: ExpenseCategoryCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new expense category"""
    
    # Check if name already exists
    existing_category = await ExpenseCategory.find_one({"name": category_data.name})
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    
    # Create category
    category = ExpenseCategory(
        name=category_data.name,
        description=category_data.description,
        isActive=category_data.is_active,
        code=category_data.code
    )
    
    await category.insert()
    
    return ExpenseCategoryResponse(
        id=str(category.id),
        name=category.name,
        description=category.description,
        is_active=category.isActive,
        code=category.code
    )


# CASH MOVEMENTS ENDPOINTS
@router.get("/cash-movements", response_model=PaginatedResponse[CashMovementResponse])
async def list_cash_movements(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    cash_cut_id: Optional[str] = Query(None, description="Filter by cash cut"),
    movement_type: Optional[str] = Query(None, description="Filter by type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_active_user)
):
    """List cash movements with pagination and filters"""
    
    # Build query
    query = {}
    
    if warehouse_id:
        query["warehouseId"] = warehouse_id
    
    if cash_cut_id:
        query["cashCutId"] = cash_cut_id
    
    if movement_type:
        query["movementType"] = movement_type
    
    # Date filter
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["movementDate"] = date_query
    
    # Aggregation pipeline
    pipeline = [
        {"$match": query},
        {"$sort": {"movementDate": -1}},
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
    total_result = await CashMovement.aggregate(total_pipeline).to_list()
    total = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    movements = await CashMovement.aggregate(pipeline).to_list()
    
    # Convert to response
    movements_response = []
    for mov in movements:
        warehouse = mov.get("warehouse", [{}])[0] if mov.get("warehouse") else {}
        user = mov.get("user", [{}])[0] if mov.get("user") else {}
        
        movements_response.append(CashMovementResponse(
            id=str(mov["_id"]),
            warehouse_id=mov["warehouseId"],
            cash_cut_id=mov.get("cashCutId"),
            movement_type=mov["movementType"],
            concept=mov["concept"],
            amount=mov["amount"],
            reference_id=mov.get("referenceId"),
            reference_type=mov.get("referenceType"),
            user_id=mov["userId"],
            movement_date=mov["movementDate"],
            observations=mov.get("notes"),
            warehouse_name=warehouse.get("name"),
            user_name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        ))
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=movements_response,
        total=total,
        page=pagination.page,
        pages=pages,
        size=pagination.size,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )