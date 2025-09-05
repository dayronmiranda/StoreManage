from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, List
from pydantic import Field, BaseModel, EmailStr
from decimal import Decimal
from pymongo import IndexModel


class Customer(Document):
    code: Indexed(str, unique=True)
    first_name: str
    last_name: Optional[str] = None
    document_type: Optional[str] = None  # id_card/nit/passport
    document_number: Optional[Indexed(str, unique=True)] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional information
    birth_date: Optional[datetime] = None
    gender: Optional[str] = None
    
    class Settings:
        collection = "customers"
        indexes = [
            IndexModel([("code", 1)], unique=True),
            IndexModel([("document_number", 1)], unique=True, sparse=True),
            IndexModel([("first_name", 1)]),
            IndexModel([("email", 1)]),
            IndexModel([("is_active", 1)]),
        ]


class PaymentMethod(Document):
    code: Indexed(str, unique=True)
    name: str  # Cash, Card, Transfer
    type: str  # cash/card/transfer
    is_active: bool = True
    requires_reference: bool = False  # For transfers, checks, etc.
    
    class Settings:
        collection = "payment_methods"
        indexes = [
            IndexModel([("code", 1)], unique=True),
            IndexModel([("is_active", 1)]),
        ]


class SaleDetail(BaseModel):  # Embedded in Sale
    product_id: str
    product_code: str  # Denormalized for history
    product_name: str  # Denormalized for history
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal
    discount: Decimal = Decimal("0")
    total: Decimal


class Sale(Document):
    sale_number: Indexed(str, unique=True)
    warehouse_id: str
    customer_id: Optional[str] = None
    user_id: str
    payment_method_id: str
    details: List[SaleDetail]  # Embedded
    subtotal: Decimal
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal
    status: str = "completed"  # pending/completed/cancelled
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    
    # Payment information
    payment_reference: Optional[str] = None
    change: Optional[Decimal] = None
    amount_received: Optional[Decimal] = None
    
    class Settings:
        collection = "sales"
        indexes = [
            IndexModel([("sale_number", 1)], unique=True),
            IndexModel([("warehouse_id", 1)]),
            IndexModel([("customer_id", 1)]),
            IndexModel([("user_id", 1)]),
            IndexModel([("sale_date", -1)]),
            IndexModel([("status", 1)]),
        ]


class Invoice(Document):
    sale_id: Indexed(str, unique=True)
    invoice_number: Indexed(str, unique=True)
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    customer_tax_data: dict  # JSON with tax data
    status: str = "issued"  # issued/cancelled
    xml_sat: Optional[str] = None
    pdf_path: Optional[str] = None
    
    # Tax information
    tax_regime: Optional[str] = None
    cfdi_use: Optional[str] = None
    
    class Settings:
        collection = "invoices"
        indexes = [
            IndexModel([("sale_id", 1)], unique=True),
            IndexModel([("invoice_number", 1)], unique=True),
            IndexModel([("issue_date", -1)]),
            IndexModel([("status", 1)]),
        ]
