from beanie import Document, Indexed
from datetime import datetime
from typing import Optional
from pydantic import Field
from decimal import Decimal
from pymongo import IndexModel


class CategoriaGasto(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    isActive: bool = True
    code: Optional[str] = None
    
    class Settings:
        collection = "expense_categories"
        indexes = [
            IndexModel([("name", 1)], unique=True),
            IndexModel([("isActive", 1)]),
        ]


class GastoOperativo(Document):
    warehouseId: str
    expenseCategoryId: str
    description: str  # Mandatory descriptive note
    amount: Decimal
    expenseDate: datetime = Field(default_factory=datetime.utcnow)
    userId: str
    imagePath: Optional[str] = None
    receiptNumber: Optional[str] = None
    supplier: Optional[str] = None
    status: str = "pending"  # pending/approved/rejected
    approvedBy: Optional[str] = None
    approvalDate: Optional[datetime] = None
    
    # Additional information
    paymentMethod: Optional[str] = None
    paymentReference: Optional[str] = None
    notes: Optional[str] = None
    
    class Settings:
        collection = "operational_expenses"
        indexes = [
            IndexModel([("warehouseId", 1)]),
            IndexModel([("expenseCategoryId", 1)]),
            IndexModel([("expenseDate", -1)]),
            IndexModel([("userId", 1)]),
            IndexModel([("status", 1)]),
        ]


class CorteCaja(Document):
    warehouseId: str
    userId: str
    cutDate: datetime
    openingTime: datetime
    closingTime: Optional[datetime] = None
    initialAmount: Decimal
    cashSales: Decimal = Decimal("0")
    totalSales: Decimal = Decimal("0")
    totalExpenses: Decimal = Decimal("0")
    expectedFinalAmount: Decimal = Decimal("0")
    actualFinalAmount: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    notes: Optional[str] = None
    status: str = "open"  # open/closed
    
    # Breakdown by payment method
    cardSales: Decimal = Decimal("0")
    transferSales: Decimal = Decimal("0")
    
    # Additional information
    transactionCount: int = 0
    averageTicket: Optional[Decimal] = None
    
    class Settings:
        collection = "cash_cuts"
        indexes = [
            IndexModel([("warehouseId", 1)]),
            IndexModel([("cutDate", -1)]),
            IndexModel([("userId", 1)]),
            IndexModel([("status", 1)]),
        ]


class MovimientoCaja(Document):
    warehouseId: str
    cashCutId: Optional[str] = None
    movementType: str  # inbound/outbound
    concept: str  # sale/expense/adjustment/initial_fund
    amount: Decimal
    referenceId: Optional[str] = None  # Sale ID, expense ID, etc.
    referenceType: Optional[str] = None  # sale/expense
    userId: str
    movementDate: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    
    class Settings:
        collection = "cash_movements"
        indexes = [
            IndexModel([("warehouseId", 1)]),
            IndexModel([("cashCutId", 1)]),
            IndexModel([("movementDate", -1)]),
            IndexModel([("movementType", 1)]),
            IndexModel([("userId", 1)]),
        ]