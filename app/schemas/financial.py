from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


# Schemas for ExpenseCategory
class ExpenseCategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    code: Optional[str] = None


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    code: Optional[str] = None


class ExpenseCategoryResponse(ExpenseCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str


# Schemas for OperationalExpense
class OperationalExpenseBase(BaseModel):
    warehouse_id: str
    expense_category_id: str
    description: str = Field(..., min_length=5, max_length=500)
    amount: Decimal = Field(..., gt=0)
    expense_date: datetime = Field(default_factory=datetime.utcnow)
    receipt_number: Optional[str] = None
    supplier: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    observations: Optional[str] = None


class OperationalExpenseCreate(OperationalExpenseBase):
    pass


class OperationalExpenseUpdate(BaseModel):
    expense_category_id: Optional[str] = None
    description: Optional[str] = Field(None, min_length=5, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[datetime] = None
    receipt_number: Optional[str] = None
    supplier: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    observations: Optional[str] = None


class OperationalExpenseResponse(OperationalExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    image_path: Optional[str] = None
    status: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    
    # Related information (optional)
    category_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    user_name: Optional[str] = None


class OperationalExpenseListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    expense_date: datetime
    description: str
    amount: Decimal
    status: str
    category_name: Optional[str] = None
    warehouse_name: Optional[str] = None


# Schema for approve/reject expense
class ApproveExpense(BaseModel):
    observations: Optional[str] = None


# Schemas for CashCut
class CashCutBase(BaseModel):
    warehouse_id: str
    cut_date: datetime
    opening_time: datetime
    initial_amount: Decimal = Field(..., ge=0)


class CashCutCreate(CashCutBase):
    pass


class CashCutResponse(CashCutBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    closing_time: Optional[datetime] = None
    cash_sales: Decimal
    total_sales: Decimal
    total_expenses: Decimal
    expected_final_amount: Decimal
    actual_final_amount: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    observations: Optional[str] = None
    status: str
    card_sales: Decimal
    transfer_sales: Decimal
    transaction_count: int
    average_ticket: Optional[Decimal] = None
    
    # Related information (optional)
    warehouse_name: Optional[str] = None
    user_name: Optional[str] = None


class CashCutListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    cut_date: datetime
    warehouse_name: Optional[str] = None
    total_sales: Decimal
    status: str
    difference: Optional[Decimal] = None


# Schema for closing cash cut
class CloseCashCut(BaseModel):
    actual_final_amount: Decimal = Field(..., ge=0)
    observations: Optional[str] = None


# Schemas for CashMovement
class CashMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    warehouse_id: str
    cash_cut_id: Optional[str] = None
    movement_type: str
    concept: str
    amount: Decimal
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    user_id: str
    movement_date: datetime
    observations: Optional[str] = None
    
    # Related information (optional)
    warehouse_name: Optional[str] = None
    user_name: Optional[str] = None